import os
import tempfile
import threading
import time
import unittest
from unittest import mock

import app


class AppSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_state_paths = (
            app.STATE_DIR,
            app.STATE_FILE,
            app.STATE_LOCK_FILE,
        )
        app.STATE_DIR = self.temp_dir.name
        app.STATE_FILE = os.path.join(self.temp_dir.name, "rotation_state.json")
        app.STATE_LOCK_FILE = os.path.join(self.temp_dir.name, "rotation_state.lock")

    def tearDown(self):
        app.STATE_DIR, app.STATE_FILE, app.STATE_LOCK_FILE = self.original_state_paths
        self.temp_dir.cleanup()

    def test_protected_endpoint_fails_closed_without_run_secret(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            response = app.app.test_client().get("/status")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"error": "service_not_configured"})

    def test_protected_endpoint_rejects_wrong_secret(self):
        with mock.patch.dict(os.environ, {"RUN_SECRET": "correct"}, clear=True):
            response = app.app.test_client().get(
                "/status", headers={"X-Run-Secret": "wrong"}
            )

        self.assertEqual(response.status_code, 401)

    def test_corrupt_state_does_not_reset_queue(self):
        with open(app.STATE_FILE, "w") as state_file:
            state_file.write("not json")

        with self.assertRaisesRegex(RuntimeError, "refusing to reset"):
            app.load_rotation_state()

    def test_state_write_is_atomic_and_readable(self):
        app.save_rotation_state(4, ["low_content"])

        self.assertEqual(
            app.load_rotation_state(),
            {"next_index": 4, "alerted": ["low_content"]},
        )
        leftovers = [
            name for name in os.listdir(self.temp_dir.name) if name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [])

    def test_railway_publish_requires_a_volume(self):
        environment = {
            "RAILWAY_ENVIRONMENT_NAME": "production",
            "RUN_SECRET": "secret",
            "IG_ACCESS_TOKEN": "token",
            "IG_BUSINESS_ACCOUNT_ID": "account",
            "PUBLIC_BASE_URL": "https://example.test",
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            response = app.app.test_client().post(
                "/run", headers={"X-Run-Secret": "secret"}
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("attach a Railway volume", response.get_json()["error"])

    def test_concurrent_runs_claim_different_posts(self):
        environment = {
            "IG_ACCESS_TOKEN": "token",
            "IG_BUSINESS_ACCOUNT_ID": "account",
            "PUBLIC_BASE_URL": "https://example.test",
        }
        results = []
        errors = []
        start = threading.Barrier(3)

        def fake_render(post, _out_dir):
            return os.path.join(self.temp_dir.name, f"{post['id']}.jpg")

        def fake_create(_user_id, _token, image_url, _caption):
            time.sleep(0.05)
            return os.path.basename(image_url).removesuffix(".jpg")

        def run_once():
            start.wait()
            try:
                results.append(app._do_run())
            except Exception as exc:  # pragma: no cover - surfaced by assertion
                errors.append(exc)

        with (
            mock.patch.dict(os.environ, environment, clear=True),
            mock.patch.object(app, "render_post", side_effect=fake_render),
            mock.patch.object(app, "create_media_container", side_effect=fake_create),
            mock.patch.object(app, "wait_for_container_ready"),
            mock.patch.object(
                app,
                "publish_media_container",
                side_effect=lambda _user_id, _token, container_id: container_id,
            ),
        ):
            threads = [threading.Thread(target=run_once) for _ in range(2)]
            for thread in threads:
                thread.start()
            start.wait()
            for thread in threads:
                thread.join(timeout=2)

        self.assertEqual(errors, [])
        self.assertEqual({result["posted"] for result in results}, {"p01", "p02"})
        self.assertEqual(app.load_rotation_state()["next_index"], 2)


if __name__ == "__main__":
    unittest.main()

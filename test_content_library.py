import unittest

from content_library import POSTS


class ContentLibraryTests(unittest.TestCase):
    def test_posts_have_unique_ids_and_supported_fields(self):
        ids = [post["id"] for post in POSTS]
        self.assertEqual(len(ids), len(set(ids)))

        for post in POSTS:
            self.assertTrue(post["caption"].strip())
            if post["style"] in {"dark_statement", "light_statement"}:
                self.assertTrue(post["headline"].strip())
            elif post["style"] == "stat":
                self.assertTrue(post["big_number"].strip())
                self.assertTrue(post["sub_line"].strip())
            else:
                self.fail(f"Unsupported style for {post['id']}: {post['style']}")

    def test_retired_website_is_not_in_post_content(self):
        for post in POSTS:
            combined_content = " ".join(
                str(value) for value in post.values() if value is not None
            ).lower()
            self.assertNotIn("propreport.com.au", combined_content, post["id"])

    def test_posts_have_no_promotional_cta(self):
        promotional_phrases = (
            "http://",
            "https://",
            "www.",
            "link in bio",
            "follow for",
            "save this post",
            "send us a dm",
            "buy now",
            "sign up",
        )
        for post in POSTS:
            caption = post["caption"].lower()
            for phrase in promotional_phrases:
                self.assertNotIn(phrase, caption, post["id"])


if __name__ == "__main__":
    unittest.main()

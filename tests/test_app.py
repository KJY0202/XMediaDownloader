import unittest

from twitter_photo_gui import build_command, clean_account


class AccountTests(unittest.TestCase):
    def test_handle_with_at(self):
        self.assertEqual(clean_account(" @openai "), "openai")

    def test_profile_url(self):
        self.assertEqual(clean_account("https://x.com/openai/"), "openai")

    def test_reject_invalid_input(self):
        with self.assertRaises(ValueError):
            clean_account("@user name")


class CommandTests(unittest.TestCase):
    def test_photo_only_disables_video(self):
        command, query = build_command("openai", "2026-01-01", "2026-02-01", "chrome", "/tmp/xmedia", "사진만")
        self.assertIn("filter:images", query)
        self.assertIn("extractor.twitter.videos=false", command)
        self.assertIn("--download-archive", command)

    def test_video_only_enables_video(self):
        command, query = build_command("openai", "2026-01-01", "2026-02-01", "chrome", "/tmp/xmedia", "영상만")
        self.assertIn("filter:videos", query)
        self.assertIn("extractor.twitter.videos=true", command)

    def test_both_media(self):
        _, query = build_command("openai", "2026-01-01", "2026-02-01", "chrome", "/tmp/xmedia", "사진 + 영상")
        self.assertIn("filter:media", query)


if __name__ == "__main__":
    unittest.main()

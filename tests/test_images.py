import unittest

from tools.images import extract_image_urls


class ImageTests(unittest.TestCase):
    def test_extracts_and_resolves_source_image_urls(self):
        html = """
        <meta property="og:image" content="/images/front.jpg">
        <script type="application/ld+json">{"image": ["https://cdn.example.test/gallery-1.jpg"]}</script>
        """
        self.assertEqual(
            extract_image_urls(html, "https://example.test/listing"),
            ["https://example.test/images/front.jpg", "https://cdn.example.test/gallery-1.jpg"],
        )


if __name__ == "__main__":
    unittest.main()
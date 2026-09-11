import unittest

from schemas import ContactScope, ContactType, Contactability, SearchCriteria
from tools.extraction import extract_listing


class ContactExtractionTests(unittest.TestCase):
    def setUp(self):
        self.criteria = SearchCriteria(beds=2, location="Ruaka", max_rent=60000)

    def contacts(self, text, url="https://listing.example/property"):
        return extract_listing("2 bedroom Ruaka apartment for rent", text, "source", url, self.criteria).contacts

    def test_phone_formats_normalize_to_kenyan_e164(self):
        contacts = self.contacts("Property inquiries: 0710570715. Office: +254 710 570 715.")
        self.assertEqual({contact.normalized_value for contact in contacts if contact.type == ContactType.PHONE}, {"+254710570715"})

    def test_context_controls_contact_scope(self):
        listing = extract_listing("2 bedroom Ruaka apartment for rent", "Property inquiries: 0710570715", "source", "https://listing.example/property", self.criteria)
        self.assertEqual(listing.contacts[0].contact_scope, ContactScope.LISTING_SPECIFIC)
        agent = extract_listing("2 bedroom Ruaka apartment for rent", "Call Jane on 0710570715", "source", "https://listing.example/property", self.criteria)
        self.assertEqual(agent.contacts[0].contact_scope, ContactScope.AGENT)
        office = extract_listing("2 bedroom Ruaka apartment for rent", "Office: 0710570715", "source", "https://listing.example/property", self.criteria)
        self.assertEqual(office.contacts[0].contact_scope, ContactScope.AGENCY_GENERAL)
        unknown = extract_listing("2 bedroom Ruaka apartment for rent", "Phone: 0710570715", "source", "https://listing.example/property", self.criteria)
        self.assertEqual(unknown.contacts[0].contact_scope, ContactScope.UNKNOWN)

    def test_whatsapp_number_and_link_are_supported(self):
        listing = extract_listing("2 bedroom Ruaka apartment for rent", "WhatsApp: +254 712 345 678", "source", "https://listing.example/property", self.criteria)
        whatsapp = next(contact for contact in listing.contacts if contact.type == ContactType.WHATSAPP)
        self.assertEqual(whatsapp.normalized_value, "+254712345678")
        self.assertEqual(listing.contactability, Contactability.WHATSAPP_WITH_NUMBER)
        link = extract_listing("2 bedroom Ruaka apartment for rent", "Chat on WhatsApp https://wa.me/254712345678", "source", "https://listing.example/property", self.criteria)
        self.assertEqual(link.contactability, Contactability.WHATSAPP_WITH_NUMBER)

    def test_whatsapp_button_without_number_does_not_invent_value(self):
        listing = extract_listing("2 bedroom Ruaka apartment for rent", "Chat on WhatsApp", "source", "https://listing.example/property", self.criteria)
        whatsapp = next(contact for contact in listing.contacts if contact.type == ContactType.WHATSAPP)
        self.assertIsNone(whatsapp.value)
        self.assertEqual(whatsapp.contact_scope, ContactScope.UNKNOWN)
        self.assertEqual(listing.contactability, Contactability.WHATSAPP_LINK_ONLY)

    def test_email_and_contact_form_preserve_provenance(self):
        listing = extract_listing("2 bedroom Ruaka apartment for rent", "Email: homes@example.test. <form action='/contact'>Send an inquiry</form>", "source", "https://listing.example/property", self.criteria)
        self.assertTrue(any(contact.type == ContactType.EMAIL for contact in listing.contacts))
        self.assertTrue(any(contact.type == ContactType.CONTACT_FORM for contact in listing.contacts))
        self.assertEqual(listing.contactability, Contactability.EMAIL)
        self.assertTrue(all(contact.source_url == "https://listing.example/property" for contact in listing.contacts))
        self.assertTrue(any(item.claim == "contact_email" for item in listing.evidence))

    def test_known_agency_domain_is_general_only(self):
        listing = extract_listing("2 bedroom apartment for rent", "Office: +254 745 321 611", "amaliproperties.co.ke", "https://amaliproperties.co.ke/property/one", self.criteria)
        self.assertEqual(listing.contacts[0].contact_scope, ContactScope.AGENCY_GENERAL)
        self.assertEqual(listing.contactability, Contactability.AGENCY_CONTACT_ONLY)


if __name__ == "__main__":
    unittest.main()
from django.test import TestCase, override_settings


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
class ErrorPageTests(TestCase):
	def test_unknown_url_displays_custom_404_page(self):
		response = self.client.get('/adresse-inconnue/')

		self.assertEqual(response.status_code, 404)
		self.assertTemplateUsed(response, 'errors/404.html')
		self.assertContains(response, 'Retour a l accueil', status_code=404)

# Create your tests here.

"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_location(self):
        """It should return a Location that reads the created account"""
        response = self.client.post(BASE_URL, json=AccountFactory().serialize())
        location = response.headers["Location"]
        self.assertTrue(location.endswith(f"/accounts/{response.get_json()['id']}"))
        self.assertEqual(self.client.get(location).get_json(), response.get_json())

    def test_list_accounts(self):
        """It should List all accounts and preserve their fields"""
        accounts = self._create_accounts(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.get_json(), [a.serialize() for a in accounts])

    def test_list_empty_accounts(self):
        """It should return an empty list when there are no accounts"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_read_account(self):
        """It should Read an account by its identifier"""
        account = self._create_accounts(1)[0]
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), account.serialize())

    def test_read_missing_account(self):
        """It should return 404 for an unknown account"""
        response = self.client.get(f"{BASE_URL}/99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.get_json()["error"], "Not Found")

    def test_update_account(self):
        """It should Update all fields and persist the same account identifier"""
        account = self._create_accounts(1)[0]
        payload = AccountFactory().serialize()
        payload["id"] = account.id + 1000
        response = self.client.put(f"{BASE_URL}/{account.id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = dict(payload, id=account.id)
        self.assertEqual(response.get_json(), expected)
        self.assertEqual(
            self.client.get(f"{BASE_URL}/{account.id}").get_json(), expected
        )
        self.assertEqual(Account.query.count(), 1)

    def test_update_missing_account(self):
        """It should return 404 when updating an unknown account"""
        response = self.client.put(
            f"{BASE_URL}/99999", json=AccountFactory().serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_bad_request(self):
        """It should reject incomplete updates without changing stored data"""
        account = self._create_accounts(1)[0]
        response = self.client.put(f"{BASE_URL}/{account.id}", json={"name": "Bad"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.get(f"{BASE_URL}/{account.id}").get_json(),
            account.serialize(),
        )

    def test_update_unsupported_media_type(self):
        """It should reject updates with an unsupported media type"""
        account = self._create_accounts(1)[0]
        response = self.client.put(
            f"{BASE_URL}/{account.id}", data="plain text", content_type="text/plain"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_account(self):
        """It should Delete an account and leave other accounts intact"""
        accounts = self._create_accounts(2)
        response = self.client.delete(f"{BASE_URL}/{accounts[0].id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")
        self.assertIsNone(Account.find(accounts[0].id))
        self.assertIsNotNone(Account.find(accounts[1].id))

    def test_delete_is_idempotent(self):
        """It should return 204 when deleting an already absent account"""
        response = self.client.delete(f"{BASE_URL}/99999")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

    def test_create_optional_fields(self):
        """It should allow an omitted phone number and date joined"""
        payload = AccountFactory().serialize()
        del payload["phone_number"]
        del payload["date_joined"]
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.get_json()["phone_number"])
        self.assertIsNotNone(response.get_json()["date_joined"])

    def test_json_with_charset(self):
        """It should accept application/json with a charset parameter"""
        response = self.client.post(
            BASE_URL,
            json=AccountFactory().serialize(),
            content_type="application/json; charset=utf-8",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_missing_content_type(self):
        """It should reject a request without a content type"""
        response = self.client.post(BASE_URL, data="{}")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_malformed_json(self):
        """It should reject malformed JSON with a JSON error response"""
        response = self.client.post(
            BASE_URL, data="{broken", content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.get_json()["error"], "Bad Request")

    def test_invalid_date(self):
        """It should reject invalid calendar dates instead of returning 500"""
        payload = AccountFactory().serialize()
        payload["date_joined"] = "2026-02-30"
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_json_array(self):
        """It should reject an array where an account object is required"""
        response = self.client.post(BASE_URL, json=[])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_supported(self):
        """It should return a JSON 405 for unsupported methods"""
        response = self.client.patch(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.get_json()["status"], 405)

    def test_internal_server_error(self):
        """It should return a JSON 500 for unexpected service errors"""
        with patch.object(Account, "all", side_effect=RuntimeError("test failure")):
            with patch.dict(app.config, PROPAGATE_EXCEPTIONS=False):
                response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.get_json()["error"], "Internal Server Error")

    def test_security_headers(self):
        """It should set Talisman security headers on the Accounts service"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertIn("default-src", response.headers["Content-Security-Policy"])
        self.assertIn("Referrer-Policy", response.headers)

    def test_cors(self):
        """It should allow browser cross-origin requests under the CORS policy"""
        origin = "https://example.com"
        response = self.client.get(BASE_URL, headers={"Origin": origin})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], origin)

    def test_cors_preflight(self):
        """It should permit JSON PUT requests in the browser CORS preflight"""
        response = self.client.options(
            f"{BASE_URL}/1",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("PUT", response.headers["Access-Control-Allow-Methods"])
        self.assertIn("Content-Type", response.headers["Access-Control-Allow-Headers"])

    def test_security_headers_on_errors(self):
        """It should preserve security and CORS headers on error responses"""
        response = self.client.get(
            f"{BASE_URL}/99999", headers={"Origin": "https://example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"], "https://example.com"
        )

from datetime import timedelta
from io import BytesIO
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from PIL import Image

from configrations.models import ContactUs

from .models import Category, Client_review, Offer, Product, ProductImage


class AuthAndProductAPITests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp()
        cls.override_media = override_settings(MEDIA_ROOT=cls.media_root)
        cls.override_media.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override_media.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user_model = get_user_model()

    def image_file(self, name="test.png"):
        buffer = BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/png")

    def test_register_returns_tokens(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "ahmed",
                "email": "ahmed@example.com",
                "first_name": "Ahmed",
                "last_name": "Ali",
                "password": "StrongPassword123",
                "password_confirm": "StrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(self.user_model.objects.filter(username="ahmed").exists())

    def test_register_validation_failure_does_not_create_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "invalid-client",
                "email": "invalid@example.com",
                "first_name": "Invalid",
                "last_name": "Client",
                "password": "StrongPassword123",
                "password_confirm": "DifferentPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)
        self.assertFalse(self.user_model.objects.filter(username="invalid-client").exists())

    def test_register_rejects_duplicate_phone_and_email_without_creating_user(self):
        self.user_model.objects.create_user(
            username="01012345678",
            email="existing@example.com",
            password="StrongPassword123",
        )
        before_count = self.user_model.objects.count()

        response = self.client.post(
            reverse("register"),
            {
                "username": "01012345678",
                "email": "existing@example.com",
                "first_name": "Duplicate",
                "last_name": "Client",
                "password": "StrongPassword123",
                "password_confirm": "StrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertEqual(self.user_model.objects.count(), before_count)

    def test_clients_are_staff_only_safe_ordered_and_searchable(self):
        older_client = self.user_model.objects.create_user(
            username="01000000001",
            email="older@example.com",
            first_name="Ahmed",
            last_name="Older",
            password="StrongPassword123",
        )
        newer_client = self.user_model.objects.create_user(
            username="01000000002",
            email="newer@example.com",
            first_name="Mariam",
            last_name="Newer",
            password="StrongPassword123",
        )
        staff = self.user_model.objects.create_user(
            username="clients-admin",
            email="staff@example.com",
            password="StrongPassword123",
            is_staff=True,
        )

        anonymous_response = self.client.get(reverse("client_list"))
        self.client.force_authenticate(user=older_client)
        non_staff_response = self.client.get(reverse("client_list"))
        self.client.force_authenticate(user=staff)
        staff_response = self.client.get(reverse("client_list"))
        search_response = self.client.get(reverse("client_list"), {"search": "Mariam"})

        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(non_staff_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(staff_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in staff_response.data],
            [newer_client.id, older_client.id],
        )
        self.assertEqual(
            set(staff_response.data[0]),
            {"id", "full_name", "email", "phone", "date_joined"},
        )
        self.assertNotIn("password", staff_response.data[0])
        self.assertNotIn(staff.id, [item["id"] for item in staff_response.data])
        self.assertNotIn("legacy_client", [item["phone"] for item in staff_response.data])
        self.assertEqual([item["id"] for item in search_response.data], [newer_client.id])

    def test_login_refresh_and_me_auth_status_codes(self):
        user = self.user_model.objects.create_user(
            username="normal-user",
            password="StrongPassword123",
            is_staff=False,
        )

        missing_me = self.client.get(reverse("auth_me"))
        login_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "normal-user", "password": "StrongPassword123"},
            format="json",
        )
        invalid_login = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "normal-user", "password": "wrong"},
            format="json",
        )
        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": login_response.data["refresh"]},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        me_response = self.client.get(reverse("auth_me"))

        self.assertEqual(missing_me.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(invalid_login.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["id"], user.id)
        self.assertFalse(me_response.data["is_staff"])

    def test_product_filtering_by_category(self):
        category = Category.objects.create(name="Desserts")
        Product.objects.create(name="Cake", description="A cake", price="12.50", category=category)
        Product.objects.create(name="Bread", description="A bread", price="5.00")

        response = self.client.get(reverse("product-list"), {"category_id": category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_arabic_prefixed_products_route_works(self):
        Product.objects.create(name="Visible Arabic route", description="A cake", price="12.50")

        response = self.client.get("/ar/api/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_review_creation_assigns_authenticated_user(self):
        user = self.user_model.objects.create_user(username="reviewer", password="StrongPassword123")
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("client-review-list"),
            {
                "review": "Excellent service",
                "review_ar": "خدمة ممتازة",
                "rating": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client_review.objects.count(), 1)
        self.assertEqual(Client_review.objects.get().user, user)

    def test_me_returns_is_staff_flag(self):
        user = self.user_model.objects.create_user(
            username="staff-user",
            email="staff@example.com",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("auth_me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_staff"])

    def test_non_staff_write_to_categories_is_forbidden(self):
        user = self.user_model.objects.create_user(username="regular-user", password="StrongPassword123")
        self.client.force_authenticate(user=user)

        response = self.client.post(reverse("category-list"), {"name": "Hidden"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_category_display_order_and_protected_delete(self):
        staff = self.user_model.objects.create_user(
            username="category-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        first = Category.objects.create(name="Second", display_order=2)
        second = Category.objects.create(name="First", display_order=1)
        Product.objects.create(name="Cake", description="A cake", price="12.50", category=first)

        list_response = self.client.get(reverse("category-list"))
        delete_response = self.client.delete(reverse("category-detail", args=[first.id]))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in list_response.data], [second.id, first.id])
        self.assertIn("display_order", list_response.data[0])
        self.assertEqual(delete_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_can_create_update_patch_and_delete_category(self):
        staff = self.user_model.objects.create_user(
            username="category-crud-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)

        create_response = self.client.post(
            reverse("category-list"),
            {"name": "Dairy", "name_ar": "ألبان", "display_order": 3},
            format="json",
        )
        put_response = self.client.put(
            reverse("category-detail", args=[create_response.data["id"]]),
            {"name": "Fresh Dairy", "name_ar": "ألبان طازجة", "display_order": 4},
            format="json",
        )
        patch_response = self.client.patch(
            reverse("category-detail", args=[create_response.data["id"]]),
            {"display_order": 5},
            format="json",
        )
        delete_response = self.client.delete(reverse("category-detail", args=[create_response.data["id"]]))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_products_visibility_filters_and_zero_quantity_rule(self):
        category = Category.objects.create(name="Desserts")
        visible = Product.objects.create(
            name="Visible",
            description="Visible product",
            price="10.00",
            category=category,
            quantity=5,
            is_available=True,
            is_visible=True,
        )
        hidden = Product.objects.create(
            name="Hidden",
            description="Hidden product",
            price="11.00",
            category=category,
            quantity=0,
            is_available=True,
            is_visible=False,
        )

        public_response = self.client.get(reverse("product-list"))
        self.assertEqual(public_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in public_response.data], [visible.id])

        staff = self.user_model.objects.create_user(
            username="product-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        staff_response = self.client.get(reverse("product-list"), {"is_visible": "false"})
        hidden.refresh_from_db()

        self.assertEqual(staff_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in staff_response.data], [hidden.id])
        self.assertFalse(hidden.is_available)

    def product_payload(self, category, **overrides):
        payload = {
            "name": "Eshta",
            "name_ar": "قشطة",
            "description": "Fresh cream dessert",
            "description_ar": "حلوى بالقشطة الطازجة",
            "price": "25.00",
            "category": category.id,
            "quantity": 10,
            "is_visible": True,
            "is_available": True,
            "display_order": 2,
        }
        payload.update(overrides)
        return payload

    def test_product_json_multipart_images_and_invalid_boolean(self):
        staff = self.user_model.objects.create_user(
            username="product-crud-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        category = Category.objects.create(name="Desserts")

        create_response = self.client.post(
            reverse("product-list"),
            self.product_payload(category),
            format="json",
        )
        product_id = create_response.data["id"]
        upload_response = self.client.patch(
            reverse("product-detail", args=[product_id]),
            {"images": [self.image_file("product-1.png")], "is_available": "false"},
            format="multipart",
        )
        image_url = upload_response.data["images"][0]["image"]
        preserve_response = self.client.patch(
            reverse("product-detail", args=[product_id]),
            {"description": "Updated without image"},
            format="json",
        )
        invalid_bool_response = self.client.get(reverse("product-list"), {"is_visible": "abc"})
        unavailable_response = self.client.patch(
            reverse("product-detail", args=[product_id]),
            {"quantity": 0, "is_available": True},
            format="json",
        )
        positive_paused_response = self.client.patch(
            reverse("product-detail", args=[product_id]),
            {"quantity": 5, "is_available": False},
            format="json",
        )
        delete_response = self.client.delete(reverse("product-detail", args=[product_id]))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["images"], [])
        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(image_url)
        self.assertEqual(preserve_response.data["images"][0]["image"], image_url)
        self.assertEqual(invalid_bool_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_visible", invalid_bool_response.data)
        self.assertFalse(unavailable_response.data["is_available"])
        self.assertFalse(positive_paused_response.data["is_available"])
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_product_create_accepts_up_to_five_images_and_rejects_six_atomically(self):
        staff = self.user_model.objects.create_user(
            username="product-image-create-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        category = Category.objects.create(name="Desserts")

        one_image_response = self.client.post(
            reverse("product-list"),
            self.product_payload(category, name="One image", images=[self.image_file("one.png")]),
            format="multipart",
        )
        five_images_response = self.client.post(
            reverse("product-list"),
            self.product_payload(
                category,
                name="Five images",
                images=[self.image_file(f"five-{index}.png") for index in range(5)],
            ),
            format="multipart",
        )
        before_count = Product.objects.count()
        six_images_response = self.client.post(
            reverse("product-list"),
            self.product_payload(
                category,
                name="Six images",
                images=[self.image_file(f"six-{index}.png") for index in range(6)],
            ),
            format="multipart",
        )

        self.assertEqual(one_image_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(one_image_response.data["images"]), 1)
        self.assertEqual(five_images_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual([image["display_order"] for image in five_images_response.data["images"]], [0, 1, 2, 3, 4])
        self.assertEqual(six_images_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", six_images_response.data)
        self.assertEqual(Product.objects.count(), before_count)

    def test_product_update_removes_adds_and_normalizes_images(self):
        staff = self.user_model.objects.create_user(
            username="product-image-update-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        category = Category.objects.create(name="Desserts")
        product = Product.objects.create(name="Multi", description="Multi", price="12.50", category=category)
        first = ProductImage.objects.create(product=product, image=self.image_file("first.png"), display_order=0)
        second = ProductImage.objects.create(product=product, image=self.image_file("second.png"), display_order=1)
        third = ProductImage.objects.create(product=product, image=self.image_file("third.png"), display_order=2)

        response = self.client.patch(
            reverse("product-detail", args=[product.id]),
            {
                "remove_image_ids": [second.id],
                "images": [self.image_file("new-a.png"), self.image_file("new-b.png")],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["images"]), 4)
        self.assertEqual([image["display_order"] for image in response.data["images"]], [0, 1, 2, 3])
        self.assertEqual([image["id"] for image in response.data["images"][:2]], [first.id, third.id])
        self.assertFalse(ProductImage.objects.filter(id=second.id).exists())

    def test_product_update_rejects_invalid_duplicate_and_oversized_image_changes_atomically(self):
        staff = self.user_model.objects.create_user(
            username="product-image-invalid-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        category = Category.objects.create(name="Desserts")
        product = Product.objects.create(name="Main", description="Main", price="12.50", category=category)
        other_product = Product.objects.create(name="Other", description="Other", price="12.50", category=category)
        existing = [
            ProductImage.objects.create(product=product, image=self.image_file(f"existing-{index}.png"), display_order=index)
            for index in range(3)
        ]
        other_image = ProductImage.objects.create(product=other_product, image=self.image_file("other.png"))

        valid_duplicate_remove = self.client.patch(
            reverse("product-detail", args=[product.id]),
            {"remove_image_ids": [existing[1].id, existing[1].id]},
            format="multipart",
        )
        too_many_response = self.client.patch(
            reverse("product-detail", args=[product.id]),
            {"images": [self.image_file(f"too-many-{index}.png") for index in range(4)]},
            format="multipart",
        )
        invalid_owner_response = self.client.patch(
            reverse("product-detail", args=[product.id]),
            {"remove_image_ids": [other_image.id]},
            format="multipart",
        )
        malformed_response = self.client.patch(
            reverse("product-detail", args=[product.id]),
            {"remove_image_ids": ["abc"]},
            format="multipart",
        )

        self.assertEqual(valid_duplicate_remove.status_code, status.HTTP_200_OK)
        self.assertEqual(len(valid_duplicate_remove.data["images"]), 2)
        self.assertEqual(too_many_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_owner_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ProductImage.objects.filter(id=other_image.id).exists())
        self.assertEqual(product.images.count(), 2)

    def test_product_json_patch_preserves_existing_images_and_response_ordering(self):
        staff = self.user_model.objects.create_user(
            username="product-image-json-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        category = Category.objects.create(name="Desserts")
        product = Product.objects.create(name="Ordered", description="Ordered", price="12.50", category=category)
        image_late = ProductImage.objects.create(product=product, image=self.image_file("late.png"), display_order=2)
        image_first = ProductImage.objects.create(product=product, image=self.image_file("first.png"), display_order=0)
        image_middle = ProductImage.objects.create(product=product, image=self.image_file("middle.png"), display_order=1)

        response = self.client.patch(
            reverse("product-detail", args=[product.id]),
            {"price": "75.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["price"], "75.00")
        self.assertEqual([image["id"] for image in response.data["images"]], [image_first.id, image_middle.id, image_late.id])
        self.assertEqual(product.images.count(), 3)

    def test_offer_public_staff_and_date_validation(self):
        today = timezone.localdate()
        current = Offer.objects.create(title="Current", is_active=True)
        Offer.objects.create(title="Inactive", is_active=False)
        Offer.objects.create(title="Future", is_active=True, start_date=today + timedelta(days=1))

        public_response = self.client.get(reverse("offer-list"))
        self.assertEqual(public_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in public_response.data], [current.id])
        self.assertTrue(public_response.data[0]["is_currently_active"])

        staff = self.user_model.objects.create_user(
            username="offer-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        staff_response = self.client.get(reverse("offer-list"))
        invalid_response = self.client.post(
            reverse("offer-list"),
            {
                "title": "Invalid",
                "start_date": today.isoformat(),
                "end_date": (today - timedelta(days=1)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(staff_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(staff_response.data), 3)
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", invalid_response.data)

    def test_offer_crud_image_removal_and_active_date_cases(self):
        today = timezone.localdate()
        Offer.objects.create(title="Expired", is_active=True, end_date=today - timedelta(days=1))
        Offer.objects.create(title="Future", is_active=True, start_date=today + timedelta(days=1))
        Offer.objects.create(title="Inactive open", is_active=False)
        open_offer = Offer.objects.create(title="Open", is_active=True)
        staff = self.user_model.objects.create_user(
            username="offer-crud-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)

        list_response = self.client.get(reverse("offer-list"))
        create_response = self.client.post(
            reverse("offer-list"),
            {
                "title": "Ramadan Offer",
                "title_ar": "عرض رمضان",
                "description": "20% off",
                "description_ar": "خصم 20٪",
                "is_active": True,
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=2)).isoformat(),
            },
            format="json",
        )
        upload_response = self.client.patch(
            reverse("offer-detail", args=[create_response.data["id"]]),
            {"image": self.image_file("offer.png")},
            format="multipart",
        )
        remove_response = self.client.patch(
            reverse("offer-detail", args=[create_response.data["id"]]),
            {"remove_image": True},
            format="json",
        )
        normal_user = self.user_model.objects.create_user(username="offer-normal", password="StrongPassword123")
        self.client.force_authenticate(user=normal_user)
        non_staff_create = self.client.post(reverse("offer-list"), {"title": "Blocked"}, format="json")
        self.client.force_authenticate(user=None)
        anonymous_create = self.client.post(reverse("offer-list"), {"title": "Blocked anon"}, format="json")
        public_response = self.client.get(reverse("offer-list"))
        self.client.force_authenticate(user=staff)
        delete_response = self.client.delete(reverse("offer-detail", args=[create_response.data["id"]]))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 4)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_response.data["is_currently_active"])
        self.assertIsNotNone(upload_response.data["image"])
        self.assertIsNone(remove_response.data["image"])
        self.assertEqual(non_staff_create.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(anonymous_create.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual({item["id"] for item in public_response.data}, {open_offer.id, create_response.data["id"]})
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_dashboard_stats_are_staff_only(self):
        Product.objects.create(
            name="Available",
            description="Available product",
            price="10.00",
            quantity=3,
            is_available=True,
        )
        Product.objects.create(name="Unavailable", description="Unavailable product", price="11.00", quantity=0)
        Offer.objects.create(title="Current offer", is_active=True)

        anonymous_response = self.client.get(reverse("dashboard_stats"))
        normal_user = self.user_model.objects.create_user(username="stats-normal", password="StrongPassword123")
        self.client.force_authenticate(user=normal_user)
        non_staff_response = self.client.get(reverse("dashboard_stats"))
        self.client.force_authenticate(user=None)
        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(non_staff_response.status_code, status.HTTP_403_FORBIDDEN)

        staff = self.user_model.objects.create_user(
            username="stats-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        response = self.client.get(reverse("dashboard_stats"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_products"], 2)
        self.assertEqual(response.data["available_products"], 1)
        self.assertEqual(response.data["unavailable_products"], 1)
        self.assertEqual(
            response.data["available_products"] + response.data["unavailable_products"],
            response.data["total_products"],
        )
        self.assertEqual(response.data["current_offers"], 1)

    def test_contact_public_create_and_staff_inbox(self):
        create_response = self.client.post(
            reverse("contact-us-list"),
            {
                "name": " Ahmed ",
                "phone_number": " +201000000000 ",
                "message": "I want to order",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactUs.objects.get().phone_number, "+201000000000")

        public_list_response = self.client.get(reverse("contact-us-list"))
        self.assertEqual(public_list_response.status_code, status.HTTP_401_UNAUTHORIZED)

        staff = self.user_model.objects.create_user(
            username="contact-admin",
            password="StrongPassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        list_response = self.client.get(reverse("contact-us-list"))
        retrieve_response = self.client.get(reverse("contact-us-detail", args=[create_response.data["id"]]))
        put_response = self.client.put(
            reverse("contact-us-detail", args=[create_response.data["id"]]),
            {"name": "Edited", "phone_number": "+201111111111", "message": "Edited"},
            format="json",
        )
        patch_response = self.client.patch(
            reverse("contact-us-detail", args=[create_response.data["id"]]),
            {"message": "Edited"},
            format="json",
        )
        delete_response = self.client.delete(reverse("contact-us-detail", args=[create_response.data["id"]]))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(patch_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_contact_validation_and_throttle_configuration(self):
        response = self.client.post(
            reverse("contact-us-list"),
            {"name": "Ahmed", "phone_number": "   ", "message": "Hello"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)
        self.assertIn("contact_submit", settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"])

    def test_review_permissions_validation_and_ordering(self):
        owner = self.user_model.objects.create_user(username="review-owner", password="StrongPassword123")
        other = self.user_model.objects.create_user(username="review-other", password="StrongPassword123")
        staff = self.user_model.objects.create_user(username="review-staff", password="StrongPassword123", is_staff=True)
        older = Client_review.objects.create(user=owner, review="Older", rating=4)
        newer = Client_review.objects.create(user=other, review="Newer", rating=5)

        public_list = self.client.get(reverse("client-review-list"))
        anonymous_create = self.client.post(reverse("client-review-list"), {"review": "No", "rating": 5}, format="json")
        self.client.force_authenticate(user=owner)
        invalid_rating = self.client.post(reverse("client-review-list"), {"review": "Bad", "rating": 6}, format="json")
        owner_patch = self.client.patch(reverse("client-review-detail", args=[older.id]), {"rating": 5}, format="json")
        self.client.force_authenticate(user=other)
        other_patch = self.client.patch(reverse("client-review-detail", args=[older.id]), {"rating": 3}, format="json")
        self.client.force_authenticate(user=staff)
        staff_delete = self.client.delete(reverse("client-review-detail", args=[newer.id]))

        self.assertEqual(public_list.status_code, status.HTTP_200_OK)
        self.assertEqual(public_list.data[0]["id"], newer.id)
        self.assertEqual(anonymous_create.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(invalid_rating.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(owner_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(other_patch.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(staff_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_schema_endpoint_contains_core_paths(self):
        response = self.client.get(reverse("schema"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema_text = response.content.decode()
        self.assertIn("/api/products/", schema_text)
        self.assertIn("/api/offers/", schema_text)
        self.assertIn("/api/contact-us/", schema_text)
        self.assertIn("/api/dashboard/stats/", schema_text)
        self.assertIn("/api/clients/", schema_text)

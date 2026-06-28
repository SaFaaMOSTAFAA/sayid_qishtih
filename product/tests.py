from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, Client_review, Product


class AuthAndProductAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

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

    def test_product_filtering_by_category(self):
        category = Category.objects.create(name="Desserts")
        Product.objects.create(name="Cake", description="A cake", price="12.50", category=category)
        Product.objects.create(name="Bread", description="A bread", price="5.00")

        response = self.client.get("/en/products/products/", {"category_id": category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_review_creation_assigns_authenticated_user(self):
        user = self.user_model.objects.create_user(username="reviewer", password="StrongPassword123")
        self.client.force_authenticate(user=user)

        response = self.client.post(
            "/en/products/client-reviews/",
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

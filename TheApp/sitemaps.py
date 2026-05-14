"""Sitemap configuration for public catalog and content pages."""

from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Section, StoreItems


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.85

    def items(self):
        return [
            "home",
            "paints",
            "about",
            "how_to_use",
            "originals",
            "prints",
        ]

    def location(self, item):
        return reverse(item)


class SectionSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.65

    def items(self):
        return Section.objects.all().order_by("id")

    def location(self, obj):
        return reverse("category_browse", kwargs={"section_id": obj.pk})


class StoreItemSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return StoreItems.objects.exclude(status=StoreItems.DRAFT).order_by("order", "pk")

    def lastmod(self, obj):
        return obj.updated

    def location(self, obj):
        return reverse("paint_detail", kwargs={"item_id": obj.pk})

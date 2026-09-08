from django.contrib import admin

from .models import IndexBuild, KnowledgeDocument


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "char_count", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "content")


@admin.register(IndexBuild)
class IndexBuildAdmin(admin.ModelAdmin):
    list_display = ("built_at", "success", "document_count", "chunk_count", "embed_model")
    readonly_fields = ("built_at", "document_count", "chunk_count", "embed_model", "success", "error")

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView


def success_response(message, data=None, status_code=200):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        },
        status=status_code,
    )


def api_documentation_view(request):
    auth_reference = [
        {
            "label": "No token",
            "description": "Public endpoint. No Authorization header required.",
        },
        {
            "label": "Access token",
            "description": "Use JWT access token in the Authorization header as Bearer <access_token>.",
        },
        {
            "label": "Refresh token",
            "description": "Used only when refreshing or blacklisting refresh sessions.",
        },
        {
            "label": "Admin access token",
            "description": "JWT access token belonging to a user whose role is admin.",
        },
        {
            "label": "Staff or admin access token",
            "description": "JWT access token for staff or admin users. Some write operations are ownership-limited for staff.",
        },
        {
            "label": "Donor access token",
            "description": "JWT access token belonging to a user whose role is donor.",
        },
    ]

    endpoint_groups = [
        {
            "title": "System",
            "description": "Service status and landing information.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/",
                    "auth": "No token",
                    "purpose": "Render the backend API documentation page in the browser.",
                    "data_needed": "No request body. Browser request only.",
                    "responses": ["HTML documentation page"],
                },
                {
                    "method": "GET",
                    "path": "/api/health/",
                    "auth": "No token",
                    "purpose": "Check whether the backend service is up.",
                    "data_needed": "No request body.",
                    "responses": ["service", "status"],
                },
            ],
        },
        {
            "title": "Users And Authentication",
            "description": "Registration, login, token lifecycle, profile access, and admin user management.",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/api/users/register/",
                    "auth": "No token",
                    "purpose": "Register a new user account.",
                    "data_needed": [
                        "username: string, unique",
                        "email: valid email, unique",
                        "phone_number: optional string",
                        "profile_image: optional file upload",
                        "role: one of admin, staff, donor",
                        "password: string, minimum 8 characters",
                    ],
                    "responses": ["id", "username", "email", "phone_number", "profile_image", "role"],
                },
                {
                    "method": "POST",
                    "path": "/api/users/login/",
                    "auth": "No token",
                    "purpose": "Authenticate a user and return JWT tokens.",
                    "data_needed": [
                        "username: existing username",
                        "password: account password",
                    ],
                    "responses": ["refresh", "access", "user"],
                },
                {
                    "method": "POST",
                    "path": "/api/users/token/refresh/",
                    "auth": "Refresh token",
                    "purpose": "Get a fresh access token using the refresh token.",
                    "data_needed": [
                        "refresh: refresh token string",
                    ],
                    "responses": ["access", "refresh when rotation is enabled"],
                },
                {
                    "method": "POST",
                    "path": "/api/users/logout/",
                    "auth": "Access token",
                    "purpose": "Blacklist a refresh token and log the current session out.",
                    "data_needed": [
                        "refresh: refresh token string",
                    ],
                    "responses": ["success message"],
                },
                {
                    "method": "GET",
                    "path": "/api/users/profile/",
                    "auth": "Access token",
                    "purpose": "Return the authenticated user profile.",
                    "data_needed": "No request body.",
                    "responses": ["id", "username", "email", "phone_number", "profile_image", "role", "is_verified", "is_active", "date_joined"],
                },
                {
                    "method": "GET",
                    "path": "/api/users/me/",
                    "auth": "Access token",
                    "purpose": "Alias of the profile endpoint.",
                    "data_needed": "No request body.",
                    "responses": ["same fields as /api/users/profile/"],
                },
                {
                    "method": "GET",
                    "path": "/api/users/admin-only/",
                    "auth": "Admin access token",
                    "purpose": "Check admin-only access.",
                    "data_needed": "No request body.",
                    "responses": ["user_id", "username", "role"],
                },
                {
                    "method": "GET",
                    "path": "/api/users/",
                    "auth": "Admin access token",
                    "purpose": "List all users.",
                    "data_needed": "No request body.",
                    "responses": ["list of user profile objects"],
                },
                {
                    "method": "GET",
                    "path": "/api/users/<id>/",
                    "auth": "Admin access token",
                    "purpose": "Fetch one user by numeric ID.",
                    "data_needed": "Path parameter id.",
                    "responses": ["user profile object"],
                },
                {
                    "method": "PUT",
                    "path": "/api/users/<id>/",
                    "auth": "Admin access token or the user's own access token",
                    "purpose": "Update a user. The current implementation uses the admin update serializer even for self-updates.",
                    "data_needed": [
                        "username",
                        "email",
                        "phone_number",
                        "profile_image",
                        "role",
                        "is_verified",
                        "is_active",
                        "first_name",
                        "last_name",
                    ],
                    "responses": ["updated user object"],
                },
                {
                    "method": "POST",
                    "path": "/api/users/claim-donor-account/",
                    "auth": "No token",
                    "purpose": "Set a password for an existing donor account by email.",
                    "data_needed": [
                        "email: donor email address",
                        "password: string, minimum 8 characters",
                        "confirm_password: must match password",
                    ],
                    "responses": ["id", "email", "username", "role"],
                },
            ],
        },
        {
            "title": "Projects And Partners",
            "description": "Partner management, project CRUD, project updates, update images, and project interest subscriptions.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/projects/partners/",
                    "auth": "No token",
                    "purpose": "List partners with filtering, search, ordering, and pagination.",
                    "data_needed": [
                        "Optional query params: is_active, search, ordering, page",
                    ],
                    "responses": ["count", "next", "previous", "results"],
                },
                {
                    "method": "POST",
                    "path": "/api/projects/partners/",
                    "auth": "Admin access token",
                    "purpose": "Create a partner.",
                    "data_needed": [
                        "name: string, unique",
                        "logo: optional file upload",
                        "website: optional URL",
                        "description: optional text",
                        "is_active: optional boolean",
                    ],
                    "responses": ["partner object"],
                },
                {
                    "method": "GET",
                    "path": "/api/projects/partners/<id>/",
                    "auth": "No token",
                    "purpose": "Fetch one partner.",
                    "data_needed": "Path parameter id.",
                    "responses": ["partner object"],
                },
                {
                    "method": "PUT/PATCH",
                    "path": "/api/projects/partners/<id>/",
                    "auth": "Admin access token",
                    "purpose": "Update a partner.",
                    "data_needed": [
                        "Any editable partner fields",
                    ],
                    "responses": ["updated partner object"],
                },
                {
                    "method": "DELETE",
                    "path": "/api/projects/partners/<id>/",
                    "auth": "Admin access token",
                    "purpose": "Delete a partner.",
                    "data_needed": "Path parameter id.",
                    "responses": ["success message"],
                },
                {
                    "method": "GET",
                    "path": "/api/projects/",
                    "auth": "No token",
                    "purpose": "List projects with filters, search, ordering, and pagination.",
                    "data_needed": [
                        "Optional query params: status, location, partners, search, ordering, page",
                    ],
                    "responses": ["count", "next", "previous", "results"],
                },
                {
                    "method": "POST",
                    "path": "/api/projects/",
                    "auth": "Staff or admin access token",
                    "purpose": "Create a project.",
                    "data_needed": [
                        "title: string",
                        "description: text",
                        "status: planning | active | completed | on_hold",
                        "budget: decimal",
                        "target_amount: decimal",
                        "start_date: YYYY-MM-DD",
                        "end_date: optional YYYY-MM-DD",
                        "location: optional string",
                        "feature_image: optional file upload",
                        "partner_ids: optional array of partner IDs",
                    ],
                    "responses": ["project object with computed funding fields"],
                },
                {
                    "method": "GET",
                    "path": "/api/projects/<id>/",
                    "auth": "No token",
                    "purpose": "Fetch one project.",
                    "data_needed": "Path parameter id.",
                    "responses": ["project object with funding metrics"],
                },
                {
                    "method": "PUT/PATCH",
                    "path": "/api/projects/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Update a project.",
                    "data_needed": [
                        "Any editable project fields",
                    ],
                    "responses": ["updated project object"],
                },
                {
                    "method": "DELETE",
                    "path": "/api/projects/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Delete a project.",
                    "data_needed": "Path parameter id.",
                    "responses": ["success message"],
                },
                {
                    "method": "GET",
                    "path": "/api/projects/updates/",
                    "auth": "No token",
                    "purpose": "List project updates.",
                    "data_needed": [
                        "Optional query params: project, search, ordering, page",
                    ],
                    "responses": ["count", "next", "previous", "results"],
                },
                {
                    "method": "POST",
                    "path": "/api/projects/updates/",
                    "auth": "Staff or admin access token",
                    "purpose": "Create a project update and trigger update emails.",
                    "data_needed": [
                        "project: project ID",
                        "title: string",
                        "description: text",
                    ],
                    "responses": ["project update object"],
                },
                {
                    "method": "GET",
                    "path": "/api/projects/updates/<id>/",
                    "auth": "No token",
                    "purpose": "Fetch one project update.",
                    "data_needed": "Path parameter id.",
                    "responses": ["project update object with images"],
                },
                {
                    "method": "PUT/PATCH",
                    "path": "/api/projects/updates/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Update a project update.",
                    "data_needed": [
                        "project: project ID",
                        "title: string",
                        "description: text",
                    ],
                    "responses": ["updated project update object"],
                },
                {
                    "method": "DELETE",
                    "path": "/api/projects/updates/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Delete a project update.",
                    "data_needed": "Path parameter id.",
                    "responses": ["success message"],
                },
                {
                    "method": "POST",
                    "path": "/api/projects/updates/images/",
                    "auth": "Staff or admin access token",
                    "purpose": "Upload an image for a project update.",
                    "data_needed": [
                        "project_update: project update ID",
                        "image: file upload",
                        "caption: optional string",
                    ],
                    "responses": ["project update image object"],
                },
                {
                    "method": "DELETE",
                    "path": "/api/projects/updates/images/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Delete a project update image.",
                    "data_needed": "Path parameter id.",
                    "responses": ["success message"],
                },
                {
                    "method": "POST",
                    "path": "/api/projects/interests/subscribe/",
                    "auth": "No token or access token",
                    "purpose": "Subscribe an email address to project updates.",
                    "data_needed": [
                        "project: project ID",
                        "name: optional string",
                        "email: valid email",
                    ],
                    "responses": ["project interest object"],
                },
                {
                    "method": "POST",
                    "path": "/api/projects/interests/unsubscribe/",
                    "auth": "No token",
                    "purpose": "Deactivate a project interest subscription.",
                    "data_needed": [
                        "project: project ID",
                        "email: subscribed email address",
                    ],
                    "responses": ["success message"],
                },
                {
                    "method": "GET",
                    "path": "/api/projects/interests/my/",
                    "auth": "Access token",
                    "purpose": "List active project interests belonging to the authenticated user.",
                    "data_needed": "No request body.",
                    "responses": ["count", "next", "previous", "results"],
                },
            ],
        },
        {
            "title": "Beneficiaries",
            "description": "Beneficiary records tied to projects plus beneficiary image uploads.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/beneficiaries/",
                    "auth": "No token",
                    "purpose": "List beneficiaries.",
                    "data_needed": [
                        "Optional query params: project, is_active, search, ordering, page",
                    ],
                    "responses": ["count", "next", "previous", "results"],
                },
                {
                    "method": "POST",
                    "path": "/api/beneficiaries/",
                    "auth": "Staff or admin access token",
                    "purpose": "Create a beneficiary under a project.",
                    "data_needed": [
                        "project: project ID",
                        "name: string",
                        "description: text",
                        "is_active: optional boolean",
                    ],
                    "responses": ["beneficiary object"],
                },
                {
                    "method": "GET",
                    "path": "/api/beneficiaries/<id>/",
                    "auth": "No token",
                    "purpose": "Fetch one beneficiary.",
                    "data_needed": "Path parameter id.",
                    "responses": ["beneficiary object with images"],
                },
                {
                    "method": "PUT/PATCH",
                    "path": "/api/beneficiaries/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Update a beneficiary.",
                    "data_needed": [
                        "project: project ID",
                        "name: string",
                        "description: text",
                        "is_active: boolean",
                    ],
                    "responses": ["updated beneficiary object"],
                },
                {
                    "method": "DELETE",
                    "path": "/api/beneficiaries/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Delete a beneficiary.",
                    "data_needed": "Path parameter id.",
                    "responses": ["success message"],
                },
                {
                    "method": "POST",
                    "path": "/api/beneficiaries/images/",
                    "auth": "Staff or admin access token",
                    "purpose": "Upload an image for a beneficiary.",
                    "data_needed": [
                        "beneficiary: beneficiary ID",
                        "image: file upload",
                        "caption: optional string",
                    ],
                    "responses": ["beneficiary image object"],
                },
                {
                    "method": "DELETE",
                    "path": "/api/beneficiaries/images/<id>/",
                    "auth": "Admin access token or owning staff access token",
                    "purpose": "Delete a beneficiary image.",
                    "data_needed": "Path parameter id.",
                    "responses": ["success message"],
                },
            ],
        },
        {
            "title": "Donations",
            "description": "Donation submission and role-filtered donation access.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/donations/",
                    "auth": "Access token",
                    "purpose": "List donations visible to the authenticated user. Admin sees all, staff sees donations for owned projects, donor sees their own.",
                    "data_needed": [
                        "Optional query params: project, status, payment_method, is_anonymous, search, ordering, page",
                    ],
                    "responses": ["count", "next", "previous", "results"],
                },
                {
                    "method": "POST",
                    "path": "/api/donations/",
                    "auth": "No token or access token",
                    "purpose": "Create a donation record.",
                    "data_needed": [
                        "project: project ID",
                        "donor_name: string",
                        "donor_email: valid email",
                        "amount: decimal greater than 0",
                        "payment_method: cash | bank | momo | card",
                        "message: optional text",
                        "is_anonymous: optional boolean",
                    ],
                    "responses": ["donation object"],
                },
                {
                    "method": "GET",
                    "path": "/api/donations/<id>/",
                    "auth": "Access token",
                    "purpose": "Fetch one visible donation by ID.",
                    "data_needed": "Path parameter id.",
                    "responses": ["donation object"],
                },
                {
                    "method": "GET",
                    "path": "/api/donations/my/",
                    "auth": "Access token",
                    "purpose": "List donations linked to the authenticated user account.",
                    "data_needed": [
                        "Optional query param: page",
                    ],
                    "responses": ["count", "next", "previous", "results"],
                },
            ],
        },
    ]

    for group in endpoint_groups:
        for endpoint in group["endpoints"]:
            endpoint["method_class"] = endpoint["method"].replace("/", "-")
            endpoint["data_needed_is_list"] = isinstance(endpoint["data_needed"], list)

    context = {
        "title": "NGO Backend API Documentation",
        "base_url": "/api/",
        "auth_reference": auth_reference,
        "endpoint_groups": endpoint_groups,
    }
    return render(request, "core/api_documentation.html", context)


class HealthCheckView(APIView):
    def get(self, request):
        return success_response(
            message="NGO backend is running properly",
            data={
                "service": "ngo-backend",
                "status": "healthy",
            },
        )

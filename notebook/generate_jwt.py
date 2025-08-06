# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: openai-realtime-console (3.12.8)
#     language: python
#     name: python3
# ---

# %%
import base64
import json
import os
import time
import uuid

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# %% [markdown]
# # JWT and JWKS Generator with RSA256
#
# This notebook demonstrates how to:
# 1. Generate RSA key pairs for signing JWTs
# 2. Create a JWKS (JSON Web Key Set) for public key distribution
# 3. Generate and sign JWT tokens using RSA256 algorithm
# 4. Verify JWT tokens
#
# JWKS is used to publish public keys that can be used to verify JWT tokens, while keeping the private keys secure for signing.


# %%
# Generate RSA key pair
def generate_rsa_key_pair():
    """Generate a new RSA key pair for JWT signing"""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Get public key
    public_key = private_key.public_key()

    return private_key, public_key


# Generate the key pair
private_key, public_key = generate_rsa_key_pair()
print("🔐 RSA key pair generated successfully!")

# Generate a unique key ID for this key pair
key_id = str(uuid.uuid4())
print(f"🆔 Key ID: {key_id}")


# %%
# Create JWKS (JSON Web Key Set)
def create_jwks(public_key, key_id):
    """Create a JWKS from a public key"""

    # Get public key numbers
    public_numbers = public_key.public_numbers()

    # Convert to base64url encoding
    def int_to_base64url(value):
        # Convert integer to bytes with proper padding
        byte_length = (value.bit_length() + 7) // 8
        value_bytes = value.to_bytes(byte_length, byteorder="big")
        # Base64url encode (no padding)
        return base64.urlsafe_b64encode(value_bytes).decode("ascii").rstrip("=")

    # Create the JWK (JSON Web Key)
    jwk = {
        "kty": "RSA",  # Key type
        "use": "sig",  # Key use (signature)
        "alg": "RS256",  # Algorithm
        "kid": key_id,  # Key ID
        "n": int_to_base64url(public_numbers.n),  # Modulus
        "e": int_to_base64url(public_numbers.e),  # Exponent
    }

    # Create JWKS (JSON Web Key Set)
    jwks = {"keys": [jwk]}

    return jwks


# Generate JWKS
jwks = create_jwks(public_key, key_id)
print("🔑 JWKS created successfully!")
print("\n📋 JWKS:")
print(json.dumps(jwks, indent=2))


# %%
# Generate JWT Token
def generate_jwt_token(private_key, key_id, payload=None, expiry_minutes=60):
    """Generate a JWT token using RSA256"""

    # Default payload if none provided
    if payload is None:
        payload = {
            "sub": "user123",  # Subject
            "name": "John Doe",  # User name
            "iat": int(time.time()),  # Issued at
            "exp": int(time.time()) + (expiry_minutes * 60),  # Expiration
            "aud": "your-audience",  # Audience
            "iss": "your-issuer",  # Issuer
        }

    # JWT header
    headers = {"alg": "RS256", "typ": "JWT", "kid": key_id}

    # Convert private key to PEM format for PyJWT
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Generate JWT
    token = jwt.encode(
        payload=payload, key=private_key_pem, algorithm="RS256", headers=headers
    )

    return token, payload


# Generate a sample JWT
sample_payload = payload = {
    "https://purl.imsglobal.org/spec/lti/claim/lti11_legacy_user_id": "f474a3f8fa0c33de4ad46cb206e2a3aee597fc51",
    "sub": "5b9f3e55-b461-a406-4527-745fd4561ab7",
    "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "66162:8daf5469c7ddd98cdad79bb1d3fdf160a669e862",
    "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
    "https://purl.imsglobal.org/spec/lti/claim/lti1p1": {
        "user_id": "f474a3f8fa0c33de4ad46cb206e2a3aee597fc51"
    },
    "tool_support_endpoint": "https://tools.canvas.ox.ac.uk",
    "iss": "https://lti.canvas.ox.ac.uk",
    "locale": "en-GB",
    "https://purl.imsglobal.org/spec/lti/claim/roles": [
        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator",
        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor",
        "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
        "http://purl.imsglobal.org/vocab/lis/v2/system/person#User",
    ],
    "nonce": "817083dc-9fae-bdda-4341-a77cd3da4f83",
    "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
        "guid": "odUmrS7riBv5kBHQyhv7XPtbq84g8YRR6N4KYbyH:canvas-lms",
        "name": "University of Oxford",
        "version": "cloud",
        "product_family_code": "canvas",
    },
    "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
        "id": "8bceeff46ef0df5cc58c9ba41a3ea275c4c39d26",
        "description": None,
        "title": "Edward Fauchon-Jones Sandpit Course",
    },
    "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "https://page-design.canvas.ox.ac.uk/modules-display?display=tiles",
    "https://purl.imsglobal.org/spec/lti/claim/context": {
        "id": "8bceeff46ef0df5cc58c9ba41a3ea275c4c39d26",
        "label": "Edward Fauchon-Jones Sandpit Course",
        "title": "Edward Fauchon-Jones Sandpit Course",
        "type": ["http://purl.imsglobal.org/vocab/lis/v2/course#CourseOffering"],
    },
    "https://purl.imsglobal.org/spec/lti/claim/custom": {
        "canvas_user_id": "793272",
        "canvas_course_id": "338729",
        "canvas_api_base_url": "https://canvas.ox.ac.uk",
        "canvas_user_prefers_high_contrast": "false",
        "com_instructure_brand_config_json_url": "https://0uqbdu11hjcvx.cloudfront.net/dist/brandable_css/282984ddd844b4e87676af421f58a80b/variables-895491bdd6ceabaf6137deaa1b310c07.json",
    },
    "aud": "100000000001941220",
    "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
    "azp": "100000000001941220",
    "iss-orig": "https://canvas.instructure.com",
    "https://purl.imsglobal.org/spec/lti/claim/launch_presentation": {
        "document_target": "iframe",
        "return_url": "https://canvas.ox.ac.uk/courses/338729",
        "locale": "en-GB",
    },
    "exp": int(time.time()) + (10 * 365 * 24 * 60 * 60),
    "iat": int(time.time()) + (9 * 365 * 24 * 60 * 60),
    "nbf": int(time.time()) + (9 * 365 * 24 * 60 * 60),
}

jwt_token, used_payload = generate_jwt_token(private_key, key_id, sample_payload)
print("🎫 JWT Token generated successfully!")
print("\n📝 Payload used:")
print(json.dumps(used_payload, indent=2))
print("\n🔗 JWT Token:")
print(jwt_token)


def save_jwt_to_file(jwt_token, key_id, tag=None):
    """Save JWT token to a file"""
    os.makedirs(key_id, exist_ok=True)
    if tag:
        filename = f"jwt_token--{tag}.txt"
    else:
        filename = "jwt_token.txt"
    with open(f"{key_id}/{filename}", "w") as f:
        f.write(jwt_token)


# Save JWT token to a file
save_jwt_to_file(jwt_token, key_id, "future-jwt")


# %%
# Verify JWT Token
def verify_jwt_token(token, public_key, audience=None, issuer=None):
    """Verify a JWT token using the public key"""

    try:
        # Convert public key to PEM format for PyJWT
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Decode and verify the token
        decoded_payload = jwt.decode(
            jwt=token,
            key=public_key_pem,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"verify_exp": True},  # Verify expiration
        )

        return True, decoded_payload, "Token is valid"

    except jwt.ExpiredSignatureError:
        return False, None, "Token has expired"
    except jwt.InvalidTokenError as e:
        return False, None, f"Token is invalid: {e!s}"
    except Exception as e:
        return False, None, f"Verification failed: {e!s}"


# Verify the generated token
is_valid, decoded_payload, message = verify_jwt_token(
    jwt_token,
    public_key,
    audience="100000000001941220",
    issuer="https://lti.canvas.ox.ac.uk",
)

print(f"✅ Verification result: {message}")
if is_valid:
    print("\n📋 Decoded payload:")
    print(json.dumps(decoded_payload, indent=2, default=str))


# %%
# Utility functions for key management
def save_keys_to_files(private_key, public_key, key_id):
    """Save keys to PEM files"""

    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Save public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    os.makedirs(key_id, exist_ok=True)

    with open(f"{key_id}/private_key.pem", "wb") as f:
        f.write(private_pem)

    with open(f"{key_id}/public_key.pem", "wb") as f:
        f.write(public_pem)

    print("🔐 Keys saved:")
    print(f"  - {key_id}/private_key.pem")
    print(f"  - {key_id}/public_key.pem")


def save_jwks_to_file(jwks, filename="jwks.json", key_id=None):
    """Save JWKS to JSON file"""

    if key_id:
        filename = f"{key_id}/{filename}"
        os.makedirs(key_id, exist_ok=True)

    with open(filename, "w") as f:
        json.dump(jwks, f)
    print(f"🔑 JWKS saved to {filename}")


# Save keys and JWKS
save_keys_to_files(private_key, public_key, key_id)
save_jwks_to_file(jwks, key_id=key_id)


# %%
# JWT Token Analysis (decode without verification)
def decode_jwt_without_verification(token):
    """Decode JWT token without verifying signature - useful for inspection"""
    try:
        # Decode header
        header = jwt.get_unverified_header(token)

        # Decode payload without verification
        payload = jwt.decode(token, options={"verify_signature": False})

        return header, payload
    except Exception as e:
        return None, f"Error decoding token: {e!s}"


# Analyze the JWT token structure
print("🔍 JWT Token Analysis:")
print("=" * 50)

header, payload = decode_jwt_without_verification(jwt_token)

print("📋 Header:")
print(json.dumps(header, indent=2))

print("\n📋 Payload:")
print(json.dumps(payload, indent=2, default=str))

# Show token parts
parts = jwt_token.split(".")
print("\n🧩 Token Structure:")
print(f"  - Header:    {parts[0][:20]}...")
print(f"  - Payload:   {parts[1][:20]}...")
print(f"  - Signature: {parts[2][:20]}...")
print(f"  - Total length: {len(jwt_token)} characters")

# %%
# Practical Example: Custom JWT for Your Application
print("🚀 Creating a custom JWT for your application...")

# Define your custom payload
custom_payload = {
    "sub": "user_12345",  # Subject (user ID)
    "email": "user@example.com",  # User email
    "roles": ["admin", "user"],  # User roles
    "permissions": ["read", "write", "delete"],  # Permissions
    "org_id": "org_789",  # Organization ID
    "iat": int(time.time()),  # Issued at
    "exp": int(time.time()) + (24 * 60 * 60),  # Expires in 24 hours
    "aud": "my-api-service",  # Your API service
    "iss": "my-auth-service",  # Your auth service
    "jti": str(uuid.uuid4()),  # JWT ID (unique)
}

# Generate custom JWT
custom_jwt, _ = generate_jwt_token(private_key, key_id, custom_payload)

print("✅ Custom JWT generated!")
print("\n🎫 Custom JWT Token:")
print(custom_jwt)

# Verify the custom JWT
is_valid, decoded, message = verify_jwt_token(
    custom_jwt, public_key, audience="my-api-service", issuer="my-auth-service"
)

print(f"\n✅ Custom JWT Verification: {message}")

print("\n" + "=" * 60)
print("📚 SUMMARY")
print("=" * 60)
print(f"🆔 Key ID: {key_id}")
print("🔐 Algorithm: RS256")
print("🔑 JWKS available for public key distribution")
print("🎫 JWT tokens can be generated and verified")
print("💾 Keys and JWKS saved to files")
print("\n💡 Next steps:")
print("  1. Use the JWKS endpoint to share public keys")
print("  2. Include the JWT in Authorization headers")
print("  3. Verify JWTs on your API endpoints")

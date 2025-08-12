# OpenAI Realtime Console

This is an example application showing how to use the [OpenAI Realtime
API](https://platform.openai.com/docs/guides/realtime) with
[WebRTC](https://platform.openai.com/docs/guides/realtime-webrtc). This fork
adds in basic LTI support through the use of JWTs through the OAuth 2.0
capability of LTI. The context for this demonstrator is to integrate support
within the Canvas LMS, and as such there may be references to Canvas LMS in this
project, but as this project only depends on LTI core capabilities, the
implementation should be adaptable to other LMS platforms as well.

This demonstrator uses the [`oxctl/ui-lti`](https://github.com/oxctl/ui-lti)
common components library to manage the JWT flow during the LTI launch process,
specifically utilising the `LtiTokenRetriever` component.

## 💻 Installation and usage

Before you begin, you'll need an OpenAI API key - [create one in the dashboard
here](https://platform.openai.com/settings/api-keys). Create a `.env` file from
the example file and set your API key in there:

```bash
cp .env.example .env
```

You can leave the `JWKS_URI` value as set in the `.env.example` file.

It is recommended to use this demonstrator project through the specified
devcontainer as there are several components require to operate all parts of
this project correctly including [Node.js](https://nodejs.org/),
[pnpm](https://pnpm.io/), [Python](https://www.python.org/), and
[Caddy](https://caddyserver.com/). As such it is recommened to install Docker
and Visual Studio Code. You can then either open the project in VS Code, open
the command palette and run the command `Dev Containers: Rebuild and Reopen in
Container` or if you have already installed the devcontainer CLI then you can
run

```bash
devcontainer open .
```

Once opened, if it is the first time opening the project in a devcontainer, the
Docker image for the devcontainer will be built and all nessesary dependencies
will be installed.

To launch the application you first need to run the Caddy server. You can start
and stop the Caddy server in the background with

```bash
caddy start
caddy stop
```

or if you want to run in the foregraound then run

```bash
caddy run
```

The Caddy server is responsible for simulating the minimal LTI environment.
Inparticular it simulates the nessesary endpoints for a full basic LTI launch
flow

1. Add the appropriate `token` and `server` query parameters to the launch URL
   to simulate and LTI launch.
2. Provide OAuth 2.0 endpoints to request JWTs from using the `token` and
   `server` query parameters.
3. Provide JWKS endpoints to expose the public keys for verifying the JWTs.

Please note that while the LTI launch `token` is a one-time token in an official
LTI launch, and as such repeated requests to the JWT request enpoints will be
refuesed when using the same `token`, in the context of this demonstrator
`token` is not a one-time token, and repeated requests to the JWT request
endpoints will succeed and return the same JWT.

Caddy exposes endpoints on port 8080. Ensure that port 8080 is forwards to your
host machine. You can check and update as nessesary by running the command
`Ports: Focus on Ports View`.

Now you should start the OpenAI Realtime Console application. You can start the
application by running

```bash
pnpm run dev
```

This should start the console application on
[http://localhost:3000](http://localhost:3000). However if you access the
application through port `3000` then the application will no longer function
correctly as initiating and OpenAI Realtime API session expects a valid JWT,
which will not be available if you access the application directly.

As such you should access the application through the Caddy server running on
port `8080`, which will handle the JWT flow for you.

The Caddy server is configured with the following launch endpoints

- <http://localhost:8080/>
- <http://localhost:8080/invalid-jwt>
- <http://localhost:8080/expired-jwt>
- <http://localhost:8080/future-jwt>

When you go to any of these endpoints, Caddy is configured to redirect your
browser to an appropriate URL that includes the appropriate `token` and `server`
query parameters, which is step 1 of the LTI launch flow. From there, once
client side logic in `LtiTokenRetriever` will fetch the JWT from the appropriate
JWT endpoint specified by the `server` query parameter. Finally when you press
the `start session` button step 3 of the LTI flow and will validate the JWT on
the server side before initiating a realtime session.

The first endpoint is a valid JWT endpoint. The remaining endpoints demonstrate
ways in which a JWT can be invalidated or rejected. If you visit any of these
endpoints, and try to start a session, it will fail, and you can see in the
terminal log for `pnpm run dev` the specific error messages for why it failed.

The LTI authentication on the server side is minimal, and does not do any checks
beyound date validity and JWT integrity. However the full JWT is available on
the server side, as such work beyound this demonstrator can and should respond
to the JWT claims and their validity.

Beyond the LTI specific features, this application is a minimal template that
uses [express](https://expressjs.com/) to serve the React frontend contained in
the [`/client`](./client) folder. The server is configured to use
[vite](https://vitejs.dev/) to build the React frontend.

This application shows how to send and receive Realtime API events over the
WebRTC data channel and configure client-side function calling. You can also
view the JSON payloads for client and server events using the logging panel in
the UI.

For a more comprehensive example, see the [OpenAI Realtime
Agents](https://github.com/openai/openai-realtime-agents) demo built with
Next.js, using an agentic architecture inspired by [OpenAI
Swarm](https://github.com/openai/swarm).

## ⚙️ JWKS and JWTs generation

This demonstrator project can be used out of the box with the JWKS and JWTs
specified in the Caddy server configuration. However it is possible to
regenerate these if you would like to, or experiment with different
configurations.

The JWKS and JWTs specified in the Caddy server were generated using the Jupyter
notebook `notebook/generate_jwt.ipynb`. The notebook itself is not committed to
the repository. Instead `jupytext` is used to keep the notebook synced with
`notebook/generate_jwt.py` that is more appropriate for Git versioning. As such
if you do not open this project in the devcontainer then you will not see the
`ipynb` and you will have to at least run

```bash
uv sync
uv run jupytext --sync notebook/generate_jwt.py
```

However as for the general installation and usage, it is recommended to use the
notebook through the devcontainer as all the required dependencies and
environment will be automatically configured and available.

Most of the cells in the notebook can be left unchanged. The main cell that will
be of relevance for regenerating and experimentation is

```python
# Generate JWT Token
```

To generate the JWTs specified in the Caddy server configuration, different
combinations of `exp`, `iat`, and `nbf`. Please note here that `nbf` is not
actually a parameter populated by LTI, but included here for completeness to
simulate a future valid JWT as the library `jsonwebtoken` does not consider
`iat` when considering future validity (ie only valid from a point in the
future). For the 4 cases specified in the Caddy configruation the following
snippets were used

```python
{
    "exp": int(time.time()) + (10 * 365 * 24 * 60 * 60),
    "iat": int(time.time()),
}

save_jwt_to_file(jwt_token, key_id)
```

```python
{
    "exp": int(time.time()) - (9 * 365 * 24 * 60 * 60),
    "iat": int(time.time()) - (10 * 365 * 24 * 60 * 60),
}

save_jwt_to_file(jwt_token, key_id, "expired-jwt")
```

```python
{
    "exp": int(time.time()) + (10 * 365 * 24 * 60 * 60),
    "iat": int(time.time()) + (9 * 365 * 24 * 60 * 60),
    "nbf": int(time.time()) + (9 * 365 * 24 * 60 * 60),
}

save_jwt_to_file(jwt_token, key_id, "future-jwt")
```

Once you have specified the JWT that you want to can run the cell. This will
save the JWT to a file under a folder named with the  `kid` specified
previously in the notebook.

The recommended flow is to specifiy a base configuration without a tag, and then
run through all the cells in the notebook expect for the final cell. This will
save out the JWT to a token file, along with the private and public parts of the
RSA used to sign the JWT, and a JWKS json file apprpriate for a `jwks.json`
endpoint.

You can then go back to the cell

```python
# Generate JWT Token
```

and modify it as required. Then rerun this cell that will reuse the previously
generated private key to sign this new JWT. You can repeat this step as many
times as you like.

At the end you will have a set of JWTs that are all signed using the same
JWKS. You can then copy the contents of the JWKS and update the
`/.well-known/jwks.json` enpoint in the Caddy server configuration. You can
then update the various `/lti/*token` endpoints with the new JWTs, or create
new JWT endpoints as required.

## 🔭 Reflection

## 🧩 Canvas LTI 1.3 Integration (New)

This project now includes optional endpoints to run as an LTI 1.3 (LTI
Advantage) tool inside Canvas while still supporting the original simulated
launch flow. The new endpoints are additive; the existing demo flow continues
to work unchanged.

### High-level flow

1. Canvas (Platform) sends users to your tool's OIDC login initiation
    endpoint `/lti/login`.
2. Your tool constructs an OIDC auth request and redirects the browser to
    Canvas' authorization endpoint.
3. Canvas authenticates the user and POSTs an `id_token` (LTI launch JWT) to
    your `/lti/launch` endpoint.
4. The tool verifies the JWT (issuer, audience / client ID, deployment ID,
    nonce) using Canvas' JWKS.
5. Dev mode convenience: the verified raw JWT is stored in `localStorage`
    (`lti_jwt`) and the user is redirected to `/` where the existing UI finds
    and uses it. (Production SHOULD exchange / persist server-side instead of
    exposing the raw token to JS.)
6. When you click “start session” the existing `/openai/token` endpoint
    validates the JWT and proceeds exactly as before.

### Do tools have to run in an iframe / have a standalone URL?

Yes. Canvas launches LTI 1.3 tools by loading a URL (the `target_link_uri`)
usually inside an iframe (e.g. Course Navigation, Assignments, Modules, etc.).
Therefore a publicly reachable standalone HTTPS URL for your tool is required.
This repository already serves a standalone web app; Canvas simply embeds it.

### Environment variables

New variables added to `.env.example`:

```text
CANVAS_ISSUER
CANVAS_AUTHORIZATION_ENDPOINT
CANVAS_JWKS_URI
CANVAS_CLIENT_ID
CANVAS_DEPLOYMENT_ID
TOOL_DOMAIN
TOOL_LOGIN_URL
TOOL_LAUNCH_URL
```

Populate them after creating the Developer Key (client ID) and after
installing the tool (deployment ID) in Canvas. During first configuration you
will not yet know `CANVAS_DEPLOYMENT_ID`; you can set it later for stricter
validation.

### Creating the Developer Key (LTI Key) in Canvas

1. Log in to Canvas as an admin.
2. Navigate: Admin > (Your Account) > Developer Keys > + Developer Key > LTI Key.
3. In the form choose “Enter JSON” and paste a version of
    `canvas-lti-config.example.json` with placeholders replaced:

    Replace `${TOOL_LOGIN_URL}` with your public login endpoint (e.g.
    `https://yourtool.example.com/lti/login`). Replace `${TOOL_LAUNCH_URL}`
    with your public launch endpoint (e.g.
    `https://yourtool.example.com/lti/launch`). Optionally remove
    `public_jwk_url` if you do not host a JWKS (this demo verifies Canvas'
    JWKS only). It may be left blank; Canvas does not need your JWKS unless
    you plan to sign services payloads or deep-link responses. You can keep
    it but point to a future endpoint.

     Minimal JSON example:

     ```jsonc
     {
         "title": "OpenAI Realtime Console",
         "scopes": [],
         "oidc_initiation_url": "https://yourtool.example.com/lti/login",
         "target_link_uri": "https://yourtool.example.com/lti/launch",
         "extensions": [
             {
                 "platform": "canvas.instructure.com",
                 "settings": {
                     "placements": [
                         {
                             "placement": "course_navigation",
                             "message_type": "LtiResourceLinkRequest",
                             "target_link_uri": "https://yourtool.example.com/lti/launch",
                             "text": "Realtime Console",
                             "default": "disabled"
                         }
                     ]
                 },
                 "privacy_level": "public"
             }
         ],
         "description": "Demo LTI 1.3 tool for OpenAI Realtime API integration"
     }
     ```

4. Save. Note the **Developer Key ID** (an integer) – this becomes your
    `CANVAS_CLIENT_ID`.
5. Switch the key state to ON.

### Installing the tool into a course (creating a Deployment)

1. Enter a test course as a teacher (or admin acting as teacher).
2. Go to Course Settings > Apps > View App Configurations > + App.
3. Choose “By Client ID” and enter the Developer Key ID from above.
4. Submit – Canvas will prompt to approve. On success the tool is installed
    and a Deployment created.
5. Copy the Deployment ID (visible if you click into the app details or via
    Admin > Settings > Apps listing). Set `CANVAS_DEPLOYMENT_ID` in `.env` and
    restart the server for stricter validation.
6. In Course Navigation (Settings > Navigation) enable the “Realtime
    Console” link if disabled.

### Running locally with Canvas

Canvas must access your tool over HTTPS with a resolvable public hostname.
For local development use a tunnelling service (e.g. `ngrok`, `cloudflared`)
pointing to your dev container port 3000.

Example: `ngrok http https://localhost:3000` (if you terminate TLS locally)
or `ngrok http 3000` for HTTP -> HTTPS tunnel. Then substitute the
generated public domain in the JSON config and environment variables.

### Launch test

1. Rebuild / restart the dev server (`pnpm run dev`).
2. From a Canvas course, click the navigation link. Canvas will perform OIDC
    login -> launch. You should be redirected finally to `/` (root) of the tool
    inside the iframe.
3. Open browser dev tools: localStorage should contain `lti_jwt`.
4. Click “start session” – the JWT should now validate server-side and the
    OpenAI realtime session begin as before.

### Security & production hardening

For simplicity, the raw LTI `id_token` is exposed to front-end code through
`localStorage`. In production you should instead:

- Verify and unpack the id_token server-side only.
- Persist session context (claims you need) in a secure server-side store
    keyed by a session cookie.
- Issue short-lived access tokens for API calls if required, not reuse the LTI
    id_token beyond initial launch.
- Implement timeout & replay protection; clear used nonce/state regularly.
- Support key rotation for Canvas JWKS.

### Duplicate vs replace behaviour

The original simulated JWT retrieval (via the `LtiTokenRetriever` component
and Caddy) still functions. The Canvas flow is additive: if
`localStorage.lti_jwt` exists it will be used automatically; otherwise the
simulated flow operates unchanged.

Managing JWTs and JWKS is fiddly, and simulating their operations within LTI
is imperfect. This demonstrator aims to provide a practical first steps into
working with JWTs, JWKS, and LTI, but should be very clear that while every
effort has been made to ensure everything is reasonable and correct, there
may be errors, or limitations of the simulation. As such you are encouraged
to trust any skepticism you may have if you see anything in this
demonstrator that doesn't make sense ✨

## License

MIT

import express from "express";
import fs from "fs";
import { createServer as createViteServer } from "vite";
import "dotenv/config";
import jwt from "jsonwebtoken";
const { JsonWebTokenError, TokenExpiredError, NotBeforeError } = jwt;
import jwksClient from "jwks-rsa";
import crypto from 'crypto';

// In-memory stores for OIDC state + nonce during LTI launches (dev only)
const oidcStore = new Map(); // state -> { nonce, created }

const app = express();
const port = process.env.PORT || 3000;
const apiKey = process.env.OPENAI_API_KEY;
const jwksUri = process.env.JWKS_URI; // demo JWKS (simulated launch)
const canvasIssuer = process.env.CANVAS_ISSUER;
const canvasAuthEndpoint = process.env.CANVAS_AUTHORIZATION_ENDPOINT;
const canvasJwksUri = process.env.CANVAS_JWKS_URI;
const canvasClientId = process.env.CANVAS_CLIENT_ID;
const canvasDeploymentId = process.env.CANVAS_DEPLOYMENT_ID;

// Basic body parsers for LTI launch POST
import bodyParser from 'body-parser';
// Canvas POSTs application/x-www-form-urlencoded by default
app.use(bodyParser.urlencoded({ extended: true }));

// Helper to build URLs with query
function buildUrl(base, params) {
  const u = new URL(base);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) u.searchParams.set(k, v);
  });
  return u.toString();
}

// LTI 1.3 OIDC login initiation endpoint
app.get('/lti/login', (req, res) => {
  if (!canvasAuthEndpoint || !canvasClientId) {
    return res.status(500).send('Canvas LTI env vars not configured');
  }
  const { iss, login_hint, target_link_uri, lti_message_hint } = req.query;
  // Accept iss optional; Canvas may omit and rely on platform config
  const state = crypto.randomUUID();
  const nonce = crypto.randomUUID();
  oidcStore.set(state, { nonce, created: Date.now() });
  const authorizeUrl = buildUrl(canvasAuthEndpoint, {
    response_type: 'id_token',
    client_id: canvasClientId,
    scope: 'openid',
    redirect_uri: process.env.TOOL_LAUNCH_URL || target_link_uri || `${req.protocol}://${req.get('host')}/lti/launch`,
    login_hint,
    state,
    response_mode: 'form_post',
    nonce,
    prompt: 'none',
    lti_message_hint,
  });
  return res.redirect(authorizeUrl);
});

// LTI 1.3 launch endpoint (receives id_token)
app.post('/lti/launch', async (req, res) => {
  try {
    const { id_token, state } = req.body;
    if (!id_token) return res.status(400).send('Missing id_token');
    const record = oidcStore.get(state);
    if (!record) return res.status(400).send('Invalid state');
    oidcStore.delete(state); // one-time use
    const decodedHeader = JSON.parse(Buffer.from(id_token.split('.')[0], 'base64url').toString());
    const kid = decodedHeader.kid;
    const client = jwksClient({ jwksUri: canvasJwksUri });
    const key = await client.getSigningKey(kid);
    const publicKey = key.getPublicKey();
    const verified = jwt.verify(id_token, publicKey, {
      audience: canvasClientId,
      issuer: canvasIssuer, // Canvas issuer
    });
    if (verified.nonce !== record.nonce) {
      return res.status(400).send('Nonce mismatch');
    }
    if (canvasDeploymentId && verified['https://purl.imsglobal.org/spec/lti/claim/deployment_id'] !== canvasDeploymentId) {
      return res.status(400).send('Deployment ID mismatch');
    }
    // Provide token to front-end (DEV ONLY). For production use secure server-side session.
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>LTI Launch</title></head><body><script>
      localStorage.setItem('lti_jwt', ${JSON.stringify(id_token)});
      window.location = '/';
    </script><noscript>Launch requires JavaScript</noscript></body></html>`;
    res.status(200).send(html);
  } catch (e) {
    console.error('LTI launch error', e);
    res.status(500).send('LTI launch failed');
  }
});

// Configure Vite middleware for React client
const vite = await createViteServer({
  server: { middlewareMode: true },
  appType: "custom",
});
app.use(vite.middlewares);

async function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Extract token after "Bearer "

  if (!token) return res.sendStatus(401); // No token provided

  console.log("JWKS URI:", jwksUri);
  const client = jwksClient({ jwksUri });
  const signingKey = await client.getSigningKey();
  const jwtPublicKey = signingKey.getPublicKey();
  jwt.verify(token, jwtPublicKey, (err, jwt) => {
    if (err) {
      if (err instanceof JsonWebTokenError) {
        console.error("Invalid JWT:", err);
        return res.sendStatus(403);
      } else if (err instanceof TokenExpiredError) {
        console.error("Expired JWT:", err);
        return res.sendStatus(403);
      } else if (err instanceof NotBeforeError) {
        console.error("Future JWT:", err);
        return res.sendStatus(403);
      } else {
        console.error("Unknown JWT error:", err);
        return res.sendStatus(403);
      }
    }
    req.jwt = jwt; // Attach decoded JWT to request
    next();
  });
}

// API route for token generation
app.get("/openai/token", authenticateToken, async (req, res) => {
  const { jwt } = req;
  console.log("JWT resource link:", jwt['https://purl.imsglobal.org/spec/lti/claim/resource_link']);
  try {
    const response = await fetch(
      "https://api.openai.com/v1/realtime/sessions",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "gpt-4o-realtime-preview-2025-06-03",
          voice: "verse",
        }),
      },
    );

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error("Token generation error:", error);
    res.status(500).json({ error: "Failed to generate token" });
  }
});

// Render the React client
app.use("*", async (req, res, next) => {
  const url = req.originalUrl;

  try {
    const template = await vite.transformIndexHtml(
      url,
      fs.readFileSync("./client/index.html", "utf-8"),
    );
    const { render } = await vite.ssrLoadModule("./client/entry-server.jsx");
    const appHtml = await render(url);
    const html = template.replace(`<!--ssr-outlet-->`, appHtml?.html);
    res.status(200).set({ "Content-Type": "text/html" }).end(html);
  } catch (e) {
    vite.ssrFixStacktrace(e);
    next(e);
  }
});

app.listen(port, () => {
  console.log(`Express server running on *:${port}`);
});

import express from "express";
import fs from "fs";
import { createServer as createViteServer } from "vite";
import "dotenv/config";
import jwt from "jsonwebtoken";
const { JsonWebTokenError, TokenExpiredError, NotBeforeError } = jwt;
import jwksClient from "jwks-rsa";

const app = express();
const port = process.env.PORT || 3000;
const apiKey = process.env.OPENAI_API_KEY;
const jwksUri = process.env.JWKS_URI;

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
          model: "gpt-4o-realtime-preview-2024-12-17",
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

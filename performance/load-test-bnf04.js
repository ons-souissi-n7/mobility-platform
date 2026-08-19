/**
 * Test de charge BNF04 — "Le temps de réponse de l'API pour les endpoints
 * courants doit être inférieur à 200 ms sous une charge de 50 utilisateurs
 * simultanés." (Rapport de conception, §2.1.2)
 *
 * Contrairement à backend/tests/test_bnf_performance.py (qui mesure des
 * requêtes séquentielles via le client de test Django, sans vraie
 * concurrence), ce script simule réellement 50 utilisateurs simultanés
 * avec k6 contre le serveur HTTP réel.
 *
 * Lancement (depuis la racine du repo, stack docker-compose.dev.yml up) :
 *
 *   docker run --rm --network mobility-platform_default \
 *     -e BASE_URL=http://backend:8000/api/v1 \
 *     -v "$(pwd)/performance:/scripts" \
 *     grafana/k6:latest run /scripts/load-test-bnf04.js
 *
 * JWT_SECRET_KEY doit correspondre à celle du backend ciblé (par défaut,
 * le secret de dev défini dans docker-compose.dev.yml) :
 *
 *   -e JWT_SECRET_KEY=... pour cibler un autre environnement.
 */

import http from "k6/http";
import { check, sleep } from "k6";
import encoding from "k6/encoding";
import crypto from "k6/crypto";

const BASE_URL = __ENV.BASE_URL || "http://backend:8000/api/v1";
const JWT_SECRET = __ENV.JWT_SECRET_KEY || "dev-jwt-secret-change-in-production";
const TARGET_VUS = Number(__ENV.TARGET_VUS || 50);
const RESPONSE_TIME_THRESHOLD_MS = Number(__ENV.RESPONSE_TIME_THRESHOLD_MS || 200);

export const options = {
  scenarios: {
    charge_nominale_bnf04: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "15s", target: TARGET_VUS },
        { duration: "30s", target: TARGET_VUS },
        { duration: "10s", target: 0 },
      ],
      gracefulRampDown: "5s",
    },
  },
  thresholds: {
    [`http_req_duration{endpoint:reference_countries}`]: [`p(95)<${RESPONSE_TIME_THRESHOLD_MS}`],
    [`http_req_duration{endpoint:academic_years}`]: [`p(95)<${RESPONSE_TIME_THRESHOLD_MS}`],
    [`http_req_duration{endpoint:students_list}`]: [`p(95)<${RESPONSE_TIME_THRESHOLD_MS}`],
    [`http_req_duration{endpoint:mobility_agreements}`]: [`p(95)<${RESPONSE_TIME_THRESHOLD_MS}`],
    [`http_req_duration{endpoint:audit_logs}`]: [`p(95)<${RESPONSE_TIME_THRESHOLD_MS}`],
    http_req_failed: ["rate<0.01"],
  },
};

// ── JWT HS256 minimal, compatible avec app.auth.authentication.verify_jwt ──

function base64UrlJson(obj) {
  return encoding.b64encode(JSON.stringify(obj), "rawurl");
}

function makeAdminJwt() {
  const now = Math.floor(Date.now() / 1000);
  const header = base64UrlJson({ alg: "HS256", typ: "JWT" });
  const body = base64UrlJson({
    sub: "k6-loadtest@n7.fr",
    email: "k6-loadtest@n7.fr",
    role: "admin",
    ine: "",
    iat: now,
    exp: now + 3600,
  });
  const signingInput = `${header}.${body}`;
  const signature = crypto.hmac("sha256", JWT_SECRET, signingInput, "base64rawurl");
  return `${signingInput}.${signature}`;
}

const ADMIN_TOKEN = makeAdminJwt();
// HOST_HEADER (optionnel) : surcharge l'en-tête Host envoyé, sans changer
// l'hôte réseau réellement contacté (BASE_URL). Utile pour cibler un
// conteneur ponctuel (ex. validation gunicorn+uvicorn isolée) dont le nom
// n'est pas dans settings.ALLOWED_HOSTS, sans modifier ALLOWED_HOSTS lui-même.
const AUTH_HEADERS = {
  Authorization: `Bearer ${ADMIN_TOKEN}`,
  ...(__ENV.HOST_HEADER ? { Host: __ENV.HOST_HEADER } : {}),
};

// ── Endpoints courants (mêmes cibles que backend/tests/test_bnf_performance.py) ──

const ENDPOINTS = [
  ["reference_countries", "/reference/countries/"],
  ["academic_years", "/academic/years/"],
  ["students_list", "/students/students/?page_size=25"],
  ["mobility_agreements", "/mobility/agreements/?page_size=25"],
  ["audit_logs", "/audit/logs/?page_size=25"],
];

export default function () {
  for (const [tag, path] of ENDPOINTS) {
    const res = http.get(`${BASE_URL}${path}`, {
      headers: AUTH_HEADERS,
      tags: { endpoint: tag },
    });
    check(res, {
      [`${tag}: statut 200`]: (r) => r.status === 200,
      [`${tag}: < ${RESPONSE_TIME_THRESHOLD_MS}ms`]: (r) => r.timings.duration < RESPONSE_TIME_THRESHOLD_MS,
    });
  }
  sleep(1);
}

#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
#  init-letsencrypt.sh
#  Первичное получение сертификата Let's Encrypt через Certbot (webroot).
#
#  Запуск (один раз при первом деплое):
#    DOMAIN_NAME=your-domain.com EMAIL=admin@your-domain.com bash scripts/init-letsencrypt.sh
# ══════════════════════════════════════════════════════════════════════════════
set -e

# ── Проверка аргументов ───────────────────────────────────────────────────────
: "${DOMAIN_NAME:?Переменная DOMAIN_NAME не задана. Пример: DOMAIN_NAME=example.com bash $0}"
: "${EMAIL:?Переменная EMAIL не задана. Пример: EMAIL=admin@example.com bash $0}"

COMPOSE_FILE="docker-compose.prod.yml"
CERTBOT_DATA="./certbot_conf"          # путь к тому certbot_conf на хосте (через inspect, если надо)
RSA_KEY_SIZE=4096
STAGING=${STAGING:-0}                  # STAGING=1 для тестирования без лимитов Let's Encrypt

echo "=================================================================="
echo "  Домен:  ${DOMAIN_NAME}"
echo "  Email:  ${EMAIL}"
echo "  Staging: ${STAGING}"
echo "=================================================================="

# ── Проверяем, нет ли уже сертификата ─────────────────────────────────────────
CERT_PATH=$(docker compose -f "$COMPOSE_FILE" run --rm --entrypoint \
    "sh -c 'ls /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem 2>/dev/null && echo ok || echo no'" \
    certbot 2>/dev/null | tail -1)

if [ "$CERT_PATH" = "ok" ]; then
    echo "[✓] Сертификат для ${DOMAIN_NAME} уже существует — пропускаем."
    exit 0
fi

# ── Создаём самоподписанный заглушка-сертификат, чтобы nginx смог стартовать ──
echo "[1/5] Создаём временный (dummy) сертификат для ${DOMAIN_NAME}..."
docker compose -f "$COMPOSE_FILE" run --rm --entrypoint \
    "openssl req -x509 -nodes -newkey rsa:${RSA_KEY_SIZE} -days 1 \
     -keyout /etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem \
     -out    /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem \
     -subj   '/CN=localhost'" \
    certbot
echo "[1/5] Временный сертификат создан."

# ── Стартуем nginx с dummy-сертификатом ───────────────────────────────────────
echo "[2/5] Запускаем nginx..."
docker compose -f "$COMPOSE_FILE" up -d nginx
echo "[2/5] Ждём готовности nginx..."
sleep 8

# ── Удаляем dummy-сертификат ──────────────────────────────────────────────────
echo "[3/5] Удаляем временный сертификат..."
docker compose -f "$COMPOSE_FILE" run --rm --entrypoint \
    "rm -rf /etc/letsencrypt/live/${DOMAIN_NAME} \
            /etc/letsencrypt/archive/${DOMAIN_NAME} \
            /etc/letsencrypt/renewal/${DOMAIN_NAME}.conf" \
    certbot
echo "[3/5] Временный сертификат удалён."

# ── Запрашиваем реальный сертификат ───────────────────────────────────────────
echo "[4/5] Запрашиваем сертификат Let's Encrypt..."

STAGING_ARG=""
[ "$STAGING" = "1" ] && STAGING_ARG="--staging"

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint \
    "certbot certonly \
      --webroot -w /var/www/certbot \
      --email ${EMAIL} \
      --agree-tos \
      --no-eff-email \
      ${STAGING_ARG} \
      -d ${DOMAIN_NAME} \
      -d www.${DOMAIN_NAME}" \
    certbot
echo "[4/5] Сертификат получен."

# ── Перезагружаем nginx с реальным сертификатом ───────────────────────────────
echo "[5/5] Перезагружаем nginx..."
docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload
echo "[5/5] nginx перезагружен."

echo ""
echo "=================================================================="
echo "  [✓] Готово! HTTPS настроен для https://${DOMAIN_NAME}"
echo "  Certbot будет автоматически обновлять сертификат каждые 12 ч."
echo "=================================================================="

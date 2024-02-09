FROM python:3.10-alpine AS builder

RUN pip install 'poetry>=1.7,<2'

WORKDIR /app
COPY poetry.lock pyproject.toml LICENSE README.md ./
COPY dns_block_blackhole dns_block_blackhole
RUN poetry build

FROM python:3.10-alpine AS runner

COPY --from=builder /app/dist /app/dist
WORKDIR /app/dist
RUN pip install /app/dist/$(ls *.whl | head -1)[all]

ENTRYPOINT [ "dns-block-blackhole" ]


# # This is where stuff is stored
# VOLUME /data

# # Install system dependencies, and certbot from pip, avoiding snapd
# RUN dnf install -y awscli2 python3 python3-pip
# RUN python3 -m venv /opt/venv && \
#     /opt/venv/bin/pip install certbot certbot-dns-route53 && \
#     ln -s /opt/venv/bin/certbot /usr/local/bin/certbot

# # Copy the entrypoint script over, and use it as the default command
# COPY certbot-aws-route53.sh /usr/local/bin/certbot-aws-route53

# # CMD [ "bash" ]
#!/bin/bash
PROG=$0

usage() {
    >&2 echo "$0"
    >&2 
    >&2 echo "Cert location: ..."
}

create_cert() {
    aws_check_certs
    ( 
        set -ex;
        certbot certonly \
            --dns-route53 \
            -d "$DOMAIN"
    )
}

renew_cert() {
    ( 
        set -ex;
        certbot renew \
            --dns-route53 \
            -d "$DOMAIN"
    )
}

aws_check_certs() {
    if [ 0 != "$(set -x; aws sts get-caller-identity; set +x; echo $?)" ]; then
        >&2 echo "ERROR: AWS credentials are invalid"
        >&2 echo "       Check that they are set properly; see: https://certbot-dns-route53.readthedocs.io/en/stable/index.html"
        exit 1
    fi
}

if [ -z "$DOMAIN" ]; then
    >&2 echo "ERROR: DOMAIN unset"
    usage
    exit 1
fi

case $ACTION in
    create)
        create_cert
        ;;
    renew)
        renew_cert
        ;;
    *)
        >&2 echo "ERROR: invalid action '$ACTION' (options: create, renew)"
        usage
        exit 1
        ;;
esac
#!/bin/sh
set -e


get_org() {
    github_api_request "https://api.github.com/orgs/$1"
}

github_api_request() {
    local verify_ssl=''
    if $SKIP_SSL_VERIFICATION; then
        verify_ssl='-k'
    fi
    curl $verify_ssl -s -H "Authorization: token $GITHUB_ACCESS_TOKEN" $@
}

next_url() {
    while read -r line; do
        if echo "$line" | grep -Eq '^Link:.*'; then
            url=$(echo "$line" | sed 's/.*\(https[^>]*\).*rel="next".*/\1/')
            if [[ "$url" = "$line" ]]; then
                url=""
            fi
            echo "$url"
            break
        fi
    done
}

split_headers() {
    awk -v bl=1 'bl{bl=0; h=($0 ~ /HTTP\/1/)} /^\r?$/{bl=1} {print $0>(h?"'"$1"'":"'"$2"'")}'
}

get_all() {
    local url="$1"
    local destfile="$2"
    local headers=$(mktemp headers.XXXXXX)
    local payloads=""
    local i=0

    while [ -n "$url" ]; do
        body=$(mktemp body.XXXXXX)
        payloads="$payloads $body"

        github_api_request -i "$url" | split_headers $headers $body

        url=$(next_url < $headers)
    done

    # combine each payload into a single JSON array
    jq -s '[.[][]]' $payloads
}

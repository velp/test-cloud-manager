CREATE TABLE rest_api_requests (
    created_at timestamp DEFAULT current_timestamp,
    remote_address cidr,
    url varchar(512),
    http_method varchar(16),
    request_body varchar(512)
);
CREATE TABLE statistics (
    date_accurate_to_the_hour timestamp NOT NULL,
    virtual_machines_number smallint NOT NULL,
    UNIQUE (date_accurate_to_the_hour)
);

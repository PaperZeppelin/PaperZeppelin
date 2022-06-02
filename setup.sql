CREATE TABLE IF NOT EXISTS guilds (
    id bigint NOT NULL,
    prefix VARCHAR(25) NOT NULL DEFAULT '-',
    verification_level smallint NOT NULL DEFAULT 0,
    mute_role bigint
);
CREATE TABLE IF NOT EXISTS mod_roles (
    guild_id bigint NOT NULL,
    role_id bigint NOT NULL
);
CREATE TABLE IF NOT EXISTS infractions (
    id BIGSERIAL PRIMARY KEY NOT NULL,
    time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    mod_id BIGINT,
    type VARCHAR(15) NOT NULL,
    reason VARCHAR(1000)
);

CREATE TABLE IF NOT EXISTS mutes (
    id BIGSERIAL PRIMARY KEY NOT NULL,
    user_id BIGINT NOT NULL,
    expired BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    guild BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id BIGSERIAL PRIMARY KEY NOT NULL,
    name VARCHAR(64) NOT NULL,
    response VARCHAR(2000) NOT NULL,
    uses INT NOT NULL DEFAULT 0,
    author_id BIGINT NOT NULL,
    author_clean VARCHAR(37) NOT NULL

);
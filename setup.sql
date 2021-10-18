CREATE TABLE IF NOT EXISTS guilds (
    id bigint NOT NULL,
    prefix VARCHAR(25) NOT NULL DEFAULT '-'
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
    mod_id BIGINT NOT NULL,
    type VARCHAR(10) NOT NULL,
    reason VARCHAR(1000)
)
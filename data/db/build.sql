CREATE TABLE IF NOT EXISTS guilds (
    GuildID INTEGER PRIMARY KEY,
    Prefix VARCHAR(30) DEFAULT "?"
);


CREATE TABLE IF NOT EXISTS main (
    UserId integer PRIMARY KEY,
    Xp integer DEFAULT 0,
    Level integer DEFAULT 0,
    XpLock text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mutes (
    UserId integer PRIMARY KEY,
    RoleIds text,
    EndTime TIMESTAMP
);
#include <uuid/uuid.h>

char uuidC[256];
uuid_t uuid;
uuid_generate(uuid);
uuid_unparse(uuid, uuidC);

import datetime
import random
import string
from loguru import logger


async def generate_random_string(length) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


async def generate_random_number() -> int:
    return random.randint(1, 3)


async def generate_splc_number() -> str:
    characters = ["@", "_"]
    return "".join(random.choice(characters) for _ in range(1))


async def validate_key(key: str) -> bool:
    y = ""
    characters = ["@", "_"]
    for x in key:
        if x not in characters:
            y += x
        else:
            try:
                index = key.index(x)
                break
            except ValueError:
                return False
    if y.isnumeric() == False:
        return False
    if len(key[index + 1 :]) != int(y):
        return False
    return True


async def encrypt(data: dict) -> str:
    if "iat" in data:
        iat = data["iat"].isoformat().replace("-", "").replace("T", "")
    else:
        iat = (
            (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))
            .isoformat()
            .replace("-", "")
            .replace("T", "")
        )
    key = ""
    x = await generate_random_number()
    key += (
        str(x)
        + (await generate_random_string(x))
        + str(data["id"])
        + (await generate_splc_number())
    )
    for y in iat:
        # if y == 'T':
        #     break
        x = await generate_random_number()
        key += (
            str(x)
            + (await generate_random_string(x))
            + y
            + (await generate_splc_number())
        )
    key = str(len(key)) + (await generate_splc_number()) + key
    return key


async def decrypt(key: str) -> dict:
    class InvalidToken(Exception):
        def __init__(self, message="Invalid Token"):
            self.message = message
            super().__init__(self.message)

    try:
        if (await validate_key(key)) == False:
            raise InvalidToken
        characters = ["@", "_"]
        for x in key:
            if x in characters:
                try:
                    index = key.index(x)
                    break
                except ValueError:
                    raise InvalidToken
        key = key[index + 1 :]
        id = ""
        key = key[(int(key[0]) + 1) :]
        for x in key:
            if x not in characters:
                id += x
            else:
                if id.isnumeric() == False:
                    logger.debug(f"id:{id}")
                    raise InvalidToken
                else:
                    id = int(id)
                    break
        return {"id": id}
    except InvalidToken as ie:
        raise ie
    except Exception as e:
        import traceback

        logger.error(traceback.format_exc())
        logger.error(e)
        raise InvalidToken

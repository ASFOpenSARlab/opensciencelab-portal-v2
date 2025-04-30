# Example from: https://docs.powertools.aws.dev/lambda/python/latest/tutorial/#simplifying-with-logger

import json
from http import HTTPStatus
import datetime

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.shared.cookies import Cookie

logger = Logger(service="APP")

# Rest is V1, HTTP is V2
app = APIGatewayHttpResolver()


@app.get("/hello/<name>")
def hello_name(name):
    logger.info(f"Request from {name} received")
    return {"message": f"hello {name}!"}


@app.get("/hello")
def hello():
    logger.info("Request from unknown received")
    return {"message": "hello unknown!"}


@app.get("/portal/hub/auth")
def portal_hub_auth():
    logger.info("Request user info")
    data = json.dumps(
        {
            "data": "gAAAAABoC9GFoQF44vqO8uIuSxnUJgblmvjZ4Cs-8EWYx1GY26b_CrY5erDOKrrzCDJTyV004IRFxAqcmAZoZHzcHLmt2bE9vZO4cwbtpYGP2uBfPjDROcOeVSgMT1Mjez-RaeYfiePmfO85S6IBJzUVGww_tsc-WnG9jQCBtO84XEhKHPmVkMgmPhVL7G6j3iG7mzcqqp0fMHr45aarNwoN1OqOpGKTiQwOdDgR0wZRKHAU7346-rMhZf9E7-hlilWnXFtGjjNEvPBHQidMSVcG5wWG8iWQK50egCxYdfwubBGXBIEZgJGgUPfp0DOgLrSUp0l23ZHqydx6j1nhdZumEfa3T8fYrtPKBANQrairQds09UTbwx0UHQ0ImpAs0uo40Zer2N_vCBzqJtHj36roiK6iGjYSDZ-fXLRa6CzfghnD8RpYU_R4k108eyyLF-yCRQCJJpuQHfGN-8S7g-uYAAk4JCa_IIZqV3vkZPzXm7Kt4CNUj6u8oJKqumQoyBt-2gNyzrYgRzgYD_cZ5_1dTAK3Td0w2Viyb_4Bv2xjjlvFeL-oIkVYoAlQ0u4S2thDE7IYwPNgjjH8Qe-BzFY48fTV48mgWoEFrrw08LQg1sif2K8YXJQwAsXMkPwvHD6S9q67EgwoCVYeMswW8LIdXG9WUOBE52xkGUwYYPjZPJPL1yLL_uEHcE4hxM4cwa9U9cD9IqRODrrs6yYdshhwacAP2BLYD2w2pvqT5ck49QCfBl1zLU2UQ01dai6vnVPCLkvJUP5g6v_C-w4ktTeDT9WUPZKnsSwZUSVjapjha2-QwdlmX3df54Nnk9ojwadaSeqe0c1KdCjO1z-5iVUdC4WsrZ6RqL6qaighMOSWRg4hP8JagHTKygLN3Jdua7wPvrmu2MGA8HDfhvWoUcR12OT6LcfAriPAifpBlgSeziVA07d-XP5XtY1HOlt0fcI7ivTfDc50lCfIU4rwp2qThfVC6H2TPbkiFUMt77XLFi7QYs9NfrK9uSdFBpBxSJ2_Q7-Uewfl1qBOuEcWU4F_1SW_7KXBhLBwf-maaxwzjQrJMGSNXgzVJyjFBSrTTm1TYoxZs6mAIWhbkdCJS5SYmz6tTacTY98bZvrPUDHhdhATt0iqCV79Tdj17CbBlR9dLrSrRhOAkxxf8EOgyeTa4jjtAbZdvw==",
            "message": "OK",
        }
    )
    return Response(
        status_code=HTTPStatus.OK.value,  # 200
        body=data,
    )


@app.get("/portal/hub/login")
def portal_hub_login():
    logger.info("Log in user")
    cookie_name = "portal-username"
    cookie_value = "\"gAAAAABoEYMwkZJeiJwc3rFWmkUzhV_DmHb5aWyQt6VcPvME2MVIjlRPnl6v3oyAs-kY6yt_grfN5yCNmudqs8MWwQZKWq6MFwPUV5sQoW1deAdYQCqR4dqtxih5qk3s_x4be1q80a_VQADdULJcwVjtMb6R4WDiooIVA0xpqg7jI-i3AmbQgWAFfo-jFNFSPqG1qUmc-tXn_EmfTMqIzffgJUVgQKEtDw==\""
    expiration_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    portal_username_cookie = Cookie(
        name=cookie_name,
        value=cookie_value,
        path="/",
        secure=False,
        http_only=True,
        expires=expiration_date
        )
    return Response(
        status_code=HTTPStatus.OK.value,  # 200
        content_type=content_types.TEXT_HTML,
        body="<html><body><p>hello</p></body></html>",
        cookies=[portal_username_cookie],
    )


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=True,
)
def lambda_handler(event, context):
    return app.resolve(event, context)

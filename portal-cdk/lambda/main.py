# Example from: https://docs.powertools.aws.dev/lambda/python/latest/tutorial/#simplifying-with-logger

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayHttpResolver
from aws_lambda_powertools.logging import correlation_paths

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
    return ('{"data": "gAAAAABoC9GFoQF44vqO8uIuSxnUJgblmvjZ4Cs-8EWYx1GY26b_Cr'
        'Y5erDOKrrzCDJTyV004IRFxAqcmAZoZHzcHLmt2bE9vZO4cwbtpYGP2uBfPjDROcOeV'
        'SgMT1Mjez-RaeYfiePmfO85S6IBJzUVGww_tsc-WnG9jQCBtO84XEhKHPmVkMgmPhVL'
        '7G6j3iG7mzcqqp0fMHr45aarNwoN1OqOpGKTiQwOdDgR0wZRKHAU7346-rMhZf9E7-h'
        'lilWnXFtGjjNEvPBHQidMSVcG5wWG8iWQK50egCxYdfwubBGXBIEZgJGgUPfp0DOgLr'
        'SUp0l23ZHqydx6j1nhdZumEfa3T8fYrtPKBANQrairQds09UTbwx0UHQ0ImpAs0uo40'
        'Zer2N_vCBzqJtHj36roiK6iGjYSDZ-fXLRa6CzfghnD8RpYU_R4k108eyyLF-yCRQCJ'
        'JpuQHfGN-8S7g-uYAAk4JCa_IIZqV3vkZPzXm7Kt4CNUj6u8oJKqumQoyBt-2gNyzrY'
        'gRzgYD_cZ5_1dTAK3Td0w2Viyb_4Bv2xjjlvFeL-oIkVYoAlQ0u4S2thDE7IYwPNgjj'
        'H8Qe-BzFY48fTV48mgWoEFrrw08LQg1sif2K8YXJQwAsXMkPwvHD6S9q67EgwoCVYeM'
        'swW8LIdXG9WUOBE52xkGUwYYPjZPJPL1yLL_uEHcE4hxM4cwa9U9cD9IqRODrrs6yYd'
        'shhwacAP2BLYD2w2pvqT5ck49QCfBl1zLU2UQ01dai6vnVPCLkvJUP5g6v_C-w4ktTe'
        'DT9WUPZKnsSwZUSVjapjha2-QwdlmX3df54Nnk9ojwadaSeqe0c1KdCjO1z-5iVUdC4'
        'WsrZ6RqL6qaighMOSWRg4hP8JagHTKygLN3Jdua7wPvrmu2MGA8HDfhvWoUcR12OT6L'
        'cfAriPAifpBlgSeziVA07d-XP5XtY1HOlt0fcI7ivTfDc50lCfIU4rwp2qThfVC6H2T'
        'PbkiFUMt77XLFi7QYs9NfrK9uSdFBpBxSJ2_Q7-Uewfl1qBOuEcWU4F_1SW_7KXBhLB'
        'wf-maaxwzjQrJMGSNXgzVJyjFBSrTTm1TYoxZs6mAIWhbkdCJS5SYmz6tTacTY98bZv'
        'rPUDHhdhATt0iqCV79Tdj17CbBlR9dLrSrRhOAkxxf8EOgyeTa4jjtAbZdvw==", "message": "OK"}')

@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=True,
)
def lambda_handler(event, context):
    return app.resolve(event, context)

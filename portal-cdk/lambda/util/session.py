from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionJwt:
    raw: Optional[str] = None
    decoded: Optional[dict] = None
    username: Optional[str] = None


@dataclass
class HubAuthUser:
    value: Optional[str] = None
    raw: Optional[str] = None


@dataclass
class PortalAuth:
    cognito: SessionJwt = field(default_factory=SessionJwt)
    portal_username: HubAuthUser = field(default_factory=HubAuthUser)
    cookies: dict = field(default_factory=dict)
    inputs: dict = field(default_factory=dict)

    def add_cognito(self, ins: dict):
        self.cognito = SessionJwt(ins)
        return self

    def add_hub_auth(self, ins: dict):
        self.portal_username = HubAuthUser(ins)
        return self


def current_session():
    if not current_session.auth:
        current_session.auth = PortalAuth()
    return dict(
        auth=current_session.auth,
        user=current_session.user,
        app=current_session.app,
    )


current_session.auth = None

# Fill in later with User Object
current_session.user = None

# Global access to the app.current_event
current_session.app = None

# print(PortalAuth().add_cognito({"raw":"blablabla"}).add_hub_auth({"value":"joe"}))
#
# my_auth = PortalAuth(
#     cognito=SessionJwt(decoded={"jwt": "bla"}),
#     portal_username=HubAuthUser(value="Joe"),
#     cookies={"portal-username": "joe"},
#     inputs=[],
# )

import main

# JWT info
valid_jwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30'
jwt_secret = 'a-string-secret-at-least-256-bits-long'
jwt_algo = 'HS256'

class TestJwt:
    def test_jwt_patched(self, lambda_context, fake_auth, helpers, monkeypatch):
        import jwt

        # verify jwt.decode is monkey patched
        res = jwt.decode("bla")

        assert res['client_id'] == "2pjp68mov6sfhqda8pjphll8cq"

    def test_jwt_unpatched(self, lambda_context, helpers):

        import jwt

        res = jwt.decode(valid_jwt, jwt_secret, algorithms=[jwt_algo])

        # Verify we get an actually decode value from real JWT.
        assert res['name'] == "John Doe"

    def test_jwt_depatched(self, lambda_context, fake_auth, helpers, monkeypatch):

        import jwt

        # verify jwt.decode is monkeypatched
        res = jwt.decode("bla")
        assert res['client_id'] == "2pjp68mov6sfhqda8pjphll8cq"

        # Monkey patch back to original
        monkeypatch.setattr("jwt.decode", helpers.jwt_decode)
        res = jwt.decode(valid_jwt, jwt_secret, algorithms=[jwt_algo])
        assert res['name'] == "John Doe"
from django.contrib.auth.models import User
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class CERNAuthenticationBackend(OIDCAuthenticationBackend):
    def get_userinfo(self, access_token, id_token, payload):
        userinfo = super().get_userinfo(access_token, id_token, payload)
        # Add the user's roles to the user information, so that they are
        # accessible from the `claims` parameter of `filter_users_by_claims`,
        # `create_user` and `update_user`.
        #
        # Note that `payload` is the verified and parsed payload of `id_token`.
        userinfo["cern_roles"] = payload["cern_roles"]
        return userinfo

    def filter_users_by_claims(self, claims):
        username = claims.get("cern_upn")
        if not username:
            return self.UserModel.objects.none()
        try:
            user = self.UserModel.objects.filter(username=username)
            return user
        except User.DoesNotExist:
            return self.UserModel.objects.none()

    def create_user(self, claims):
        username = claims["cern_upn"]
        email = claims["email"]
        user = self.UserModel.objects.create_user(username, email=email)
        return self.update_user(user, claims)

    def update_user(self, user, claims):
        user.first_name = claims["given_name"]
        user.last_name = claims["family_name"]
        user.save()
        return user

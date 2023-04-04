from src.resources.auth import RegisterResource, LoginResource
from src.services.user import UserService
from src.base.middleware import AuthMiddleware
import settings
from src import app
from src.base.utils import add_resource

app.wsgi_app = AuthMiddleware(app.wsgi_app, settings=settings,
                              ignored_endpoints=["/register", "/login", "/options", "/features",
                                                 "/apartments"])

register = RegisterResource.initiate(serializers=RegisterResource.serializers, service_klass=UserService)
login = LoginResource.initiate(serializers=LoginResource.serializers, service_klass=UserService)


add_resource(register, '/register')
add_resource(login, '/login')


if __name__ == '__main__':
    app.run(debug=True, port=3000)


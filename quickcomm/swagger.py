from drf_yasg.inspectors import SwaggerAutoSchema

class CompoundTagsSchema(SwaggerAutoSchema):

    # See https://github.com/axnsan12/drf-yasg/issues/56
    pass

from drf_yasg import openapi
from drf_yasg.utils import guess_response_status
from drf_yasg.inspectors import SwaggerAutoSchema

# https://github.com/axnsan12/drf-yasg/issues/575#issuecomment-873554448
class CustomSwaggerAutoSchema(SwaggerAutoSchema):

    def get_tags(self, operation_keys):
        return [' > '.join(operation_keys[:-1])]
    def get_responses(self):
        response_serializers = self.get_response_serializers()
        response_schemas = self.get_response_schemas(response_serializers)

        paginator = self.overrides.get('paginator', None)
        if paginator and self.has_list_response():
            method = self.method.lower()
            default_response_status = str(guess_response_status(method))
            if default_response_status in response_schemas:
                response_schemas[default_response_status] = openapi.Response(
                    description=response_schemas[default_response_status].description,
                    schema=self.get_paginated_response(
                        response_schemas[default_response_status].schema
                    )
                )

        return openapi.Responses(responses=response_schemas)

    def get_paginated_response(self, response_schema):
        return self.probe_inspectors(self.paginator_inspectors, 'get_paginated_response',
                                     self._get_paginator(), response_schema=response_schema)

    def get_pagination_parameters(self):
        if not self.should_page():
            return []

        return self.probe_inspectors(self.paginator_inspectors, 'get_paginator_parameters',
                                     self._get_paginator()) or []

    def should_page(self):
        return self._get_paginator() and self.has_list_response()

    def _get_paginator(self):
        return self.overrides.get('paginator') or getattr(self.view, 'paginator', None)
#include "{{PROJECT_NAME}}_I.h"
#include "{{PROJECT_NAME}}.h"

namespace {{NAMESPACE}} {

{{PROJECT_NAME}}::{{PROJECT_NAME}}() {}

{{PROJECT_NAME}}::~{{PROJECT_NAME}}() {}

int {{PROJECT_NAME}}::performOperation(int input) {
    {{PROJECT_NAME}}Impl impl;
    return impl.calculate(input);
}

std::string {{PROJECT_NAME}}::getWelcomeMessage() const {
    return "Welcome to {{PROJECT_NAME}}!";
}

} // namespace {{NAMESPACE}}

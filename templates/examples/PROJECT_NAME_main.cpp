#include <iostream>
#include "{{PROJECT_NAME}}_I.h"

int main() {
    {{NAMESPACE}}::{{PROJECT_NAME}} module;
    std::cout << module.getWelcomeMessage() << std::endl;
    std::cout << "Operation result (10): " << module.performOperation(10) << std::endl;
    return 0;
}

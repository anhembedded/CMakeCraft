#pragma once

#include "{{PROJECT_NAME}}_I.h"

namespace {{NAMESPACE}} {

// Internal implementation details for {{PROJECT_NAME}}
class {{PROJECT_NAME}}Impl {
public:
    int calculate(int val) { return val * 2; }
};

} // namespace {{NAMESPACE}}

#include <gtest/gtest.h>
#include "{{PROJECT_NAME}}_I.h"

using namespace {{NAMESPACE}};

TEST({{PROJECT_NAME}}Test, BasicOperation) {
    {{PROJECT_NAME}} module;
    EXPECT_EQ(module.performOperation(21), 42);
}

TEST({{PROJECT_NAME}}Test, WelcomeMessage) {
    {{PROJECT_NAME}} module;
    EXPECT_EQ(module.getWelcomeMessage(), "Welcome to {{PROJECT_NAME}}!");
}

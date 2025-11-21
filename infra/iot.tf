resource "aws_iot_topic_rule" "to_lambda" {
    name        = "iot_to_lambda"
    description = "Send IoT Core messages to Lambda"
    enabled     = true
    sql         = "SELECT * FROM 'sensors/#'"
    sql_version = "2016-03-23"

    lambda {
        function_arn = aws_lambda_function.iot_handler.arn
    }
}

resource "aws_lambda_permission" "allow_iot" {
    statement_id  = "AllowIoTInvocation"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.iot_handler.function_name
    principal     = "iot.amazonaws.com"
    source_arn    = aws_iot_topic_rule.to_lambda.arn
}
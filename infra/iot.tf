# Data source to get AWS IoT Core endpoint
data "aws_iot_endpoint" "iot_endpoint" {
  endpoint_type = "iot:Data-ATS"
}

# IoT Topic Rule - Routes messages from sensors/# to Lambda
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

# Lambda Permission - Allows IoT Core to invoke the Lambda function
resource "aws_lambda_permission" "allow_iot" {
  statement_id  = "AllowIoTInvocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.iot_handler.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.to_lambda.arn
}

# =========================================================
# IoT Device Registration & Authentication
# =========================================================

# IoT Policy - Defines what devices are allowed to do
resource "aws_iot_policy" "sensor_policy" {
  name = "sensor_device_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iot:Connect"
        ]
        Resource = "arn:aws:iot:*:*:client/$${iot:Connection.Thing.ThingName}"
      },
      {
        Effect = "Allow"
        Action = [
          "iot:Publish"
        ]
        Resource = [
          "arn:aws:iot:*:*:topic/sensors/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iot:Subscribe"
        ]
        Resource = [
          "arn:aws:iot:*:*:topicfilter/sensors/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iot:Receive"
        ]
        Resource = [
          "arn:aws:iot:*:*:topic/sensors/*"
        ]
      }
    ]
  })
}

# IoT Certificate - X.509 certificate for device authentication
resource "aws_iot_certificate" "sensor_cert" {
  active = true
}

# IoT Thing - Represents a physical device
resource "aws_iot_thing" "sensor_device" {
  name = "sensor-device-001"

  attributes = {
    device_type = "occupancy_sensor"
    location    = "restroom_unit_1"
  }
}

# Attach Policy to Certificate
resource "aws_iot_policy_attachment" "sensor_policy_attach" {
  policy = aws_iot_policy.sensor_policy.name
  target = aws_iot_certificate.sensor_cert.arn
}

# Attach Certificate to Thing
resource "aws_iot_thing_principal_attachment" "sensor_thing_attach" {
  principal = aws_iot_certificate.sensor_cert.arn
  thing     = aws_iot_thing.sensor_device.name
}

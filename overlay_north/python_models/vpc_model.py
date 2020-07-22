class VPC:
    def __init__(self, vpcId, vpcName, customerId, host, scaleFactor: str):
        self.vpcId = vpcId
        self.vpcName = vpcName
        self.customerId = customerId
        self.host = host
        self.scaleFactor = scaleFactor

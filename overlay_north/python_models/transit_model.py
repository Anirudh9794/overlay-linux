from overlay_north.python_models import tunnel_model
from typing import List


class Transit_Model:
    def __init__(self, transit_id, customer_id, host, reliability_factor, tunnels: List[tunnel_model.Tunnel_Model]):
        self.transit_id = transit_id
        self.customer_id = customer_id
        self.host = host
        self.reliability_factor = reliability_factor
        self.tunnels = tunnels

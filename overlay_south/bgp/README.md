1. Copy and run the Docker image called  "quagga_docker_file". 
    ```bash
    $ sudo docker build -t quagga_docker -f quagga_docker_file .
    ```

    Can verify image using
    ```bash
    $ sudo docker images
    ```

    This creates container **bgp-router-1** from the quagga_docker image defined above.
    ```bash
    $ docker run --privileged --name bgp-router-1 -d -ti -p 2606:2606 -p 180:180 quagga_docker
    ```

    To create a container with a defined bgpd.conf located in /home/ece792/bgp/conf/test.conf file...
    ```bash
    $ docker run -v /home/ece792/bgp/conf/test.conf:/etc/quagga/bgpd.conf --privileged --name bgp-router-1 -d -ti -p 2606:2606 -p 180:180 quagga_docker
    ```

    Can verify container using
    ```bash
    $ docker ps -a
    ```

    Then run the container **bgp-router-1**
    ```bash
    $ docker exec -it bgp-router-1 bash
    ```
2. Once inside the container...

    Edit the daemon file to enable zebra and bgp
    ```bash
    $ cd /etc/quagga
    $ vim daemons
    $ vim bgpd.conf
    $ vim zebra.conf
    ```

    Start Quagga service
    ```bash
    $ service quagga start
    ```
    Stop Quagga service
    ```bash
    $ service quagga stop
    ```
    **FORCE Stop** Quagga service
    ```bash
    $ ps -ef | grep quagga
    $ kill -9 "UID number"
    ```

    Get login info for router. Default password is: "zebra"
    ```bash
    $ cat /etc/quagga/bgpd.conf
    ```

    Get the router port...
    ```bash
    $ nmap localhost
    ```

    Finally login to the router!
    ```bash
    $ telnet localhost <port>
    ```

3. For the transit router bgp-router-1

    ![The topology](https://github.ncsu.edu/ashamas/overlay-linux/blob/bgp/overlay_south/bgp/topology.png)

    Need to ensure that bgp-router-1 changes next hop to itself when advertising routes to neighbors.
    
    Assuming the router is already active...
    ```bash
    $ telnet localhost 2605
    bgpd> enable
    bgpd> conf t
    bgpd (config)> router bgp 100
    bgpd (config-router)> neighbor 172.17.0.3 next-hop-self
    bgpd (config-router)> neighbor 172.17.0.4 next-hop-self
    bgpd (config-router)> end
    bgpd> clear ip bgp 172.17.0.3 soft out
    ```
    The very last line tells the router to send out the new updates!

    To see BGP route table in the bgpd daemon
    ```bash
    $ telnet localhost 2605
    bgpd> enable
    bgpd> show ip bgp
    ```

    To see BGP route table in the zebra daemon
    ```bash
    $ telnet localhost 2601
    Router> enable
    Router> show ip route bgp show ip bgp summary
    ```

    To see BGP summary in bgpd daemon
    ```bash
    $ telnet localhost 2605
    Router> enable
    Router> show ip bgp summary
    ```

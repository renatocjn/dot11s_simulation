#include "ns3/wifi-module.h"
#include "ns3/mesh-module.h"
#include "ns3/mobility-module.h"
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/hwmp-protocol.h"
#include "ns3/applications-module.h"
#include "ns3/random-variable.h"
#include "ns3/wifi-phy.h"
#include "ns3/flow-monitor.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/ipv4-flow-classifier.h"
#include "ns3/boolean.h"
#include "ns3/object.h"
#include "ns3/enum.h"
#include "ns3/double.h"
#include "ns3/simulator.h"
#include "ns3/log.h"
#include <cmath>
#include "ns3/uinteger.h"
#include "ns3/traced-value.h"
#include "ns3/trace-source-accessor.h"
#include "../src/mesh/model/dot11s/airtime-metric.h"
#include "ns3/mesh-wifi-interface-mac.h"
#include "ns3/wifi-remote-station-manager.h"
#include "ns3/wifi-mode.h"
#include <iostream>
#include <sstream>
#include <fstream>
#include <vector>

using namespace ns3;
NS_LOG_COMPONENT_DEFINE ("ConstantPosition");

class MeshTest {
public:
	/// Init test
	MeshTest();
	/// Run test
	int Run();

private:
	int m_nnodes;
	double m_step;
	double m_randomStart;
	double m_totalTime;
	uint16_t m_packetSize;
	double m_packetInterval;
	uint32_t m_nIfaces;
	bool m_chan;
	bool m_pcap;
	uint8_t port;
	int maxPacketCount;
	std::string m_stack;
	std::string m_root;

	/// List of network nodes
	NodeContainer nodes;
	/// List of all mesh point devices
	NetDeviceContainer meshDevices;
	//Addresses of interfaces:
	Ipv4InterfaceContainer interfaces;
	// MeshHelper. Report is not static methods
	MeshHelper mesh;

private:
	/// Create nodes and setup their mobility
	void CreateNodes();
	/// Install internet m_stack on nodes
	void InstallInternetStack();
	/// Install applications
	void InstallApplication();

};

MeshTest::MeshTest() :
m_nnodes(4), m_step(10.0), m_randomStart(0.1), m_totalTime(100),
m_packetSize(1024), m_packetInterval(0.1), m_nIfaces(1),
m_chan(true), m_pcap(false), maxPacketCount(1000),
m_stack("ns3::Dot11sStack"), m_root("00:00:00:00:00:01") {
}

void MeshTest::CreateNodes() {

	// Calculate nnodes stations random topology
	nodes.Create(m_nnodes);

	// Configure YansWifiChannel
	YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default();

	YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default();
	wifiPhy.SetChannel(wifiChannel.Create());
	mesh = MeshHelper::Default();

	mesh.SetStackInstaller(m_stack, "Root",
						   Mac48AddressValue(Mac48Address(m_root.c_str())));

	if (m_chan) {
		mesh.SetSpreadInterfaceChannels(MeshHelper::SPREAD_CHANNELS);
	} else {
		mesh.SetSpreadInterfaceChannels(MeshHelper::ZERO_CHANNEL);
	}

	mesh.SetMacType("RandomStart", TimeValue(Seconds(m_randomStart)));
	// Set number of interfaces - default is single-interface mesh point
	mesh.SetNumberOfInterfaces(m_nIfaces);
	// Install protocols and return container if MeshPointDevices
	meshDevices = mesh.Install(wifiPhy, nodes);
	// Setup mobility

	//        wifiPhy.EnableAsciiAll (std::string("mp-"));
	MobilityHelper mobility;
	mobility.SetPositionAllocator("ns3::RandomRectanglePositionAllocator", "X",
								  RandomVariableValue(UniformVariable(0, m_step)), "Y",
								  RandomVariableValue(UniformVariable(0, m_step / 2)));
	mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");

	mobility.Install(nodes);

	for (NodeContainer::Iterator j = nodes.Begin(); j != nodes.End(); ++j) {
		Ptr<Node> object = *j;
		Ptr<MobilityModel> position = object->GetObject<MobilityModel> ();
		// NS_ASSERT (position != 0);// to verify the condition
		Vector pos = position->GetPosition();
		std::cout << "x=" << pos.x << ", y=" << pos.y << std::endl;
	}

	if (m_pcap)
		wifiPhy.EnablePcapAll(std::string("mp-"));

	// Create mesh helper and set stack installer to it
	// Stack installer creates all needed protocols and install them to device

}

void MeshTest::InstallInternetStack()

{
	//Install the internet protocol stack on all nodes
	InternetStackHelper internetStack;
	internetStack.Install(nodes);
	//Assign IP addresses to the devices interfaces (m_nIfaces)
	Ipv4AddressHelper address;
	address.SetBase("192.168.1.0", "255.255.255.0");
	interfaces = address.Assign(meshDevices);
}

void MeshTest::InstallApplication() {

	//
	// Create one UdpServer applications on node 0
	//


	//
	// Create UdpClient application to send UDP datagrams.
	//

	for (int i = 1; i < m_nnodes; i += 2) {

		int server_id = i - 1;
		uint16_t port = 2000 + i;
		UdpServerHelper server(port);
		ApplicationContainer apps = server.Install(nodes.Get(server_id));
		apps.Start(Seconds(1.0));
		apps.Stop(Seconds(80.0));

		UdpClientHelper client(interfaces.GetAddress(server_id), port);
		client.SetAttribute("MaxPackets", UintegerValue(maxPacketCount));
		client.SetAttribute("Interval", TimeValue(Seconds(m_packetInterval)));
		client.SetAttribute("PacketSize", UintegerValue(m_packetSize));
		ApplicationContainer apps2 = client.Install(nodes.Get(i));
		apps2.Start(Seconds(2.0));
		apps2.Stop(Seconds(50.0));
	}

}

int MeshTest::Run() {
	CreateNodes();
	InstallInternetStack();
	InstallApplication();
	Simulator::Stop(Seconds(m_totalTime));
	Simulator::Run();
	Simulator::Destroy();
	return 0;
}

int main(int argc, char *argv[]) {
	LogComponentEnable("UdpClient", LOG_LEVEL_INFO);
	LogComponentEnable("UdpServer", LOG_LEVEL_INFO);
	MeshTest t;
	return t.Run();
}

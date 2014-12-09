/* -*- mode:c++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */

//	Arquvo inicialmente copiado dos exemplos do modulo de mesh do ns3
//	Tem como objetivo simular topologias de mesh

#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/applications-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mesh-module.h"
#include "ns3/mobility-module.h"
#include "ns3/mesh-helper.h"
#include "ns3/random-variable.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/hwmp-protocol.h"
#include "ns3/netanim-module.h"

#include <ctime>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <fstream>
#include <set>
#include <cmath>
#include <list>
#include <unistd.h>
#include <cstdio>
#include <sstream>
#include <string>

#define EOL std::endl //EOL = End Of Line

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("TestMeshScript");
class MeshTest
{
public:
	MeshTest ();

	void Configure (int argc, char ** argv);

	int Run ();

private:
	unsigned int m_numberNodes;
	unsigned int m_nFlows;
	double    m_randomStart;
	double    m_totalTime;
	unsigned int m_packetsPerSec;
	double    m_packetInterval;
	uint16_t  m_packetSize;
	uint32_t  m_nIfaces;
	bool      m_chan;
	bool      m_pcap;
	int       m_seed;
	std::string m_stack;
	std::string m_root;
	std::string m_positionsFilePath;
	unsigned int m_serverId;
	double m_waitTime;
	double m_radius;
	unsigned m_numberOfTopologiesToBeGenerated;
	unsigned int m_xsize;
	unsigned int m_ysize;

	Ptr<FlowMonitor> m_flowMonitor;
	NodeContainer nodes;
	NetDeviceContainer meshDevices;
	Ipv4InterfaceContainer interfaces;
	MeshHelper mesh;
	std::list<Vector> m_positions;

private:
	void CreateNodes ();
	void InstallInternetStack ();
	void InstallApplication ();
	void Report ();
	void loadPositions();
	void parsePositions();
	double* splitAndCorrectType(std::string line);
	void PopulateArpCache ();

};

MeshTest::MeshTest () :
	m_numberNodes (50),
	m_nFlows (1),
	m_randomStart (0.1),
	m_totalTime (100.0),
	m_packetsPerSec(10),
	m_packetInterval (0.1),
	m_packetSize (1024),
	m_nIfaces (1),
	m_chan (true),
	m_pcap (false),
	m_seed (-1),
	m_stack ("ns3::Dot11sStack"),
	m_root ("00:00:00:00:00:01"),
	m_positionsFilePath (""),
	m_serverId (0),
	m_waitTime(5.0) {}

int main (int argc, char *argv[]) {
	MeshTest t;
	t.Configure (argc, argv);
	return t.Run ();
}

void MeshTest::Configure (int argc, char *argv[]) {
	srand(time(NULL));
	CommandLine cmd;
    
    int m_step;
    
	cmd.AddValue ("x-size",  "Size of the x axis of the rectangle [100]", m_xsize);
	cmd.AddValue ("y-size",  "Size of the y axis of the rectangle [100]", m_ysize);

	cmd.AddValue ("flows", "Number of flows in the simulation. [1]", m_nFlows);

	cmd.AddValue ("start",  "Maximum random start delay, seconds. [0.1 s]", m_randomStart);
	cmd.AddValue ("time",  "Simulation time, seconds [100 s]", m_totalTime);

	cmd.AddValue ("packets-per-sec",  "Number of packets to be send per sec [10]", m_packetsPerSec);
	cmd.AddValue ("packet-size",  "Size of packets in UDP ping", m_packetSize);
	cmd.AddValue ("interfaces", "Number of radio interfaces used by each mesh point. [1]", m_nIfaces);
	cmd.AddValue ("channels",   "Use different frequency channels for different interfaces. [1]", m_chan);
	cmd.AddValue ("wait-time", "Time waited before starting applications [5 s]", m_waitTime);

	cmd.AddValue ("positions-file", "path to file with positions for node placement", m_positionsFilePath);

	cmd.AddValue ("pcap",   "Enable PCAP traces on interfaces. [0]", m_pcap);

	cmd.AddValue ("seed", "Seed for the generation of the simulation, must be positive, if not set it will be a random number generated from time", m_seed);
	cmd.AddValue ("step", "Distance between nodes in the grid", m_step);

	cmd.AddValue ("radius", "Radius of the disk that the mesh points are randomly located. [300 m]", m_radius);
	cmd.AddValue ("number-of-nodes",  "Number of nodes in the simulation. [50]", m_numberNodes);

	cmd.AddValue ("number-of-topologies", "Number of topologies to be generated [3]", m_numberOfTopologiesToBeGenerated);

	cmd.Parse (argc, argv);

	NS_LOG_DEBUG ("Random Disk area with " << m_numberNodes << " nodes");
	NS_LOG_DEBUG ("Simulation time: " << m_totalTime << " s");

	if (m_seed == -1) {
		m_seed = rand();
	}
	SeedManager::SetSeed(m_seed);
}

int MeshTest::Run () {
 	//std::cout << "CreateNodes" << EOL;
	CreateNodes ();
 	//std::cout << "loadPositions" << EOL;
	loadPositions();
 	//std::cout << "InstallInternetStack" << EOL;
	InstallInternetStack ();
 	//std::cout << "InstallApplication" << EOL;
	InstallApplication ();
 	//std::cout << "PopulateArpCache" << EOL;
	PopulateArpCache ();

	FlowMonitorHelper fmh;
	fmh.InstallAll();
	m_flowMonitor = fmh.GetMonitor();
 	
	Simulator::Schedule (Seconds (m_totalTime), &MeshTest::Report, this);
	Simulator::Stop (Seconds (m_totalTime));
 	//std::cout << "Run" << EOL;
 	
 	FILE* fp2 = std::fopen("tmp", "w");
 	for (uint32_t i=0; i<nodes.GetN(); i++) {
		ns3::Vector p = nodes.Get(i)->GetObject<MobilityModel>()->GetPosition();
		fprintf(fp2, "%d|%f|%f\n", i, p.x, p.y);
	}
 	
	Simulator::Run ();
	Simulator::Destroy ();

	m_flowMonitor->CheckForLostPackets();
	m_flowMonitor->SerializeToXmlFile("FlowMonitorResults.xml", false, false);

	FILE* fp = std::fopen("seed.txt", "w");
	std::fprintf(fp, "%d\n", m_seed);
	std::fclose(fp);

	//std::cout << "Ended!!" << EOL;
	return 0;
}

void MeshTest::CreateNodes () {
	//m_serverId = m_seed % m_numberNodes;
	
	parsePositions();
	m_numberNodes = m_positions.size();

	nodes = NodeContainer();
	nodes.Create (m_numberNodes);

	YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
	YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
	wifiPhy.SetChannel (wifiChannel.Create ());

	mesh = MeshHelper::Default ();

	mesh.SetStackInstaller (m_stack, "Root", Mac48AddressValue (Mac48Address (m_root.c_str ())));

	if (m_chan) {
		mesh.SetSpreadInterfaceChannels (MeshHelper::SPREAD_CHANNELS);
	}
	else {
		mesh.SetSpreadInterfaceChannels (MeshHelper::ZERO_CHANNEL);
	}

	mesh.SetMacType ("RandomStart", TimeValue (Seconds (m_randomStart)));
	mesh.SetNumberOfInterfaces (m_nIfaces);

	meshDevices = mesh.Install (wifiPhy, nodes);

	if (m_pcap)
		wifiPhy.EnablePcapAll (std::string ("mp-"));

	Ptr<NetDevice> nd = meshDevices.Get(m_serverId);
	Ptr<MeshPointDevice> mpd = nd->GetObject<MeshPointDevice>();
	Ptr<MeshL2RoutingProtocol> protocol = mpd->GetObject<MeshL2RoutingProtocol>();
	Ptr<dot11s::HwmpProtocol> hwmp = mpd->GetObject<dot11s::HwmpProtocol>();
	hwmp->SetRoot();
}

void MeshTest::InstallInternetStack () {
	InternetStackHelper internetStack;
	internetStack.Install (nodes);
	Ipv4AddressHelper address;
	address.SetBase ("10.1.1.0", "255.255.255.0");
	interfaces = address.Assign (meshDevices);
}

void MeshTest::InstallApplication () {
	double totalTransmittingTime = m_totalTime - 5.0;
	m_packetInterval = ( (double) m_nFlows ) / ( (double) m_packetsPerSec ) ;
	UdpServerHelper echoServer (9);
	ApplicationContainer serverApps = echoServer.Install (nodes.Get (m_serverId));
	serverApps.Start (Seconds (m_waitTime));
	serverApps.Stop (Seconds (totalTransmittingTime));

	UdpClientHelper echoClient (interfaces.GetAddress (m_serverId), 9);
	echoClient.SetAttribute ("MaxPackets", UintegerValue ((uint32_t)((totalTransmittingTime-m_waitTime)*(1/m_packetInterval))));
	echoClient.SetAttribute ("Interval", RandomVariableValue(ExponentialVariable(m_packetInterval)));
	echoClient.SetAttribute ("PacketSize", UintegerValue (m_packetSize));

	int start = m_seed % m_numberNodes;
	std::set<int> clientIds;

// 	std::cout << "CLient Loop" << EOL;
	do {
		int tmp = (start + rand()) % m_numberNodes;
		clientIds.insert(tmp);
// 		std::cout << start << EOL;
	} while (clientIds.size() < m_nFlows);
// 	std::cout << "CLient Loop END" << EOL;

	NodeContainer clients;
	FILE* fp = std::fopen("clients.txt", "w");
	for (std::set<int>::iterator it = clientIds.begin(); it != clientIds.end(); it++) {
		clients.Add(nodes.Get (*it));
		std::fprintf(fp, "%d\n", *it);
	}
	std::fclose(fp);

	ApplicationContainer clientApps = echoClient.Install (clients);
	clientApps.Start (Seconds (m_waitTime));
	clientApps.Stop (Seconds (totalTransmittingTime));
}

void MeshTest::loadPositions() {
	MobilityHelper mobility;

	Ptr<ListPositionAllocator> positionAllocator = CreateObject<ListPositionAllocator>();
	for (std::list<Vector>::iterator p=m_positions.begin(); p != m_positions.end(); ++p) {
		positionAllocator->Add(*p);
	}

	mobility.SetPositionAllocator(positionAllocator);

	mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
	mobility.Install (nodes);
}

void MeshTest::parsePositions() {
	std::ifstream inputFile (m_positionsFilePath.c_str());
	std::string line;

	while( inputFile.good() ) {
		std::getline(inputFile, line);

		double* splittedLine = this->splitAndCorrectType(line);
// 		double node_id = splittedLine[0];
		double x_pos = splittedLine[1];
		double y_pos = splittedLine[2];

		m_positions.push_back( Vector((double) x_pos, (double) y_pos, 0.0) );
	}
}

double* MeshTest::splitAndCorrectType(std::string line) {
	double* result = new double[3];

	double curr_position = 0;
	double nextDelim = line.find('|');
	std::string substr = line.substr(curr_position, nextDelim);

	std::stringstream ss1(substr);
	ss1 >> result[0];

	curr_position = nextDelim+1;
	nextDelim = line.find('|', curr_position);
	substr = line.substr(curr_position, nextDelim);

	std::stringstream ss2(substr);
	ss2 >> result[1];

	curr_position = nextDelim+1;
	nextDelim = line.length();
	substr = line.substr(curr_position, nextDelim);

	std::stringstream ss3(substr);
	ss3 >> result[2];

	return result;
}

void MeshTest::Report () {
	unsigned n (0);
	for (NetDeviceContainer::Iterator i = meshDevices.Begin (); i != meshDevices.End (); ++i, ++n)
	{
		std::ostringstream os;
		os << "mp-report-" << n << ".xml";
		std::ofstream of;
		of.open (os.str ().c_str ());
		if (!of.is_open ())
		{
			std::cerr << "Error: Can't open file " << os.str () << EOL;
			return;
		}
		mesh.Report (*i, of);
		of.close ();
	}
}

void MeshTest::PopulateArpCache ()
{
	Ptr<ArpCache> arp = CreateObject<ArpCache> ();
	arp->SetAliveTimeout (Seconds(3600 * 24 * 365));
	for (NodeList::Iterator i = NodeList::Begin(); i != NodeList::End(); ++i)
	{
		Ptr<Ipv4L3Protocol> ip = (*i)->GetObject<Ipv4L3Protocol> ();
		NS_ASSERT(ip !=0);
		ObjectVectorValue interfaces;
		ip->GetAttribute("InterfaceList", interfaces);

		for(ObjectVectorValue::Iterator j = interfaces.Begin(); j != interfaces.End (); j ++)
		{
			//Ptr<Ipv4Interface> ipIface = (*j)->GetObject<Ipv4Interface> ();
			Ptr<Ipv4Interface> ipIface = (j->second)->GetObject<Ipv4Interface> ();
			NS_ASSERT(ipIface != 0);
			Ptr<NetDevice> device = ipIface->GetDevice();
			NS_ASSERT(device != 0);
			Mac48Address addr = Mac48Address::ConvertFrom(device->GetAddress ());
			for(uint32_t k = 0; k < ipIface -> GetNAddresses (); k ++)
			{
				Ipv4Address ipAddr = ipIface->GetAddress (k).GetLocal();
				if(ipAddr == Ipv4Address::GetLoopback())
					continue;
				ArpCache::Entry * entry = arp->Add(ipAddr);
				entry->MarkWaitReply(0);
				entry->MarkAlive(addr);
			}
		}

	}

	for (NodeList::Iterator i = NodeList::Begin(); i != NodeList::End(); ++i)
	{
		Ptr<Ipv4L3Protocol> ip = (*i)->GetObject<Ipv4L3Protocol> ();
		NS_ASSERT(ip !=0);
		ObjectVectorValue interfaces;
		ip->GetAttribute("InterfaceList", interfaces);
		for(ObjectVectorValue::Iterator j = interfaces.Begin(); j != interfaces.End (); j ++)
		{
			//Ptr<Ipv4Interface> ipIface = (*j)->GetObject<Ipv4Interface> ();
			Ptr<Ipv4Interface> ipIface = (j->second)->GetObject<Ipv4Interface> ();
			ipIface->SetAttribute("ArpCache", PointerValue(arp));
		}
	}
}

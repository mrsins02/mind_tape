class MemoryGraph {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.width = this.container.clientWidth || 800;
    this.height = this.container.clientHeight || 600;
    this.nodes = [];
    this.links = [];
    this.simulation = null;
    this.svg = null;
    this.g = null;
    this.zoom = null;
    this.colorScale = d3.scaleOrdinal(d3.schemeCategory10);
    
    this.init();
  }
  
  init() {
    this.svg = d3.select(this.container)
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', [0, 0, this.width, this.height]);
    
    this.g = this.svg.append('g');
    
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        this.g.attr('transform', event.transform);
      });
    
    this.svg.call(this.zoom);
    
    this.simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collision', d3.forceCollide().radius(30));
    
    this.linksGroup = this.g.append('g').attr('class', 'links');
    this.nodesGroup = this.g.append('g').attr('class', 'nodes');
    this.labelsGroup = this.g.append('g').attr('class', 'labels');
    
    window.addEventListener('resize', () => this.resize());
  }
  
  resize() {
    this.width = this.container.clientWidth || 800;
    this.height = this.container.clientHeight || 600;
    this.svg.attr('viewBox', [0, 0, this.width, this.height]);
    this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
    this.simulation.alpha(0.3).restart();
  }
  
  async loadData(threshold = 0.7) {
    try {
      const data = await API.getGraph(threshold);
      this.nodes = data.nodes;
      this.links = data.edges.map(e => ({
        source: e.source,
        target: e.target,
        weight: e.weight
      }));
      this.render();
      this.updateStats();
    } catch (error) {
      console.error('Failed to load graph:', error);
    }
  }
  
  render() {
    const links = this.linksGroup.selectAll('line')
      .data(this.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
    
    links.exit().remove();
    
    const linksEnter = links.enter().append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6);
    
    this.linkElements = linksEnter.merge(links)
      .attr('stroke-width', d => Math.sqrt(d.weight) * 2);
    
    const nodes = this.nodesGroup.selectAll('circle')
      .data(this.nodes, d => d.id);
    
    nodes.exit().remove();
    
    const nodesEnter = nodes.enter().append('circle')
      .attr('class', 'node')
      .attr('r', d => 8 + d.size * 4)
      .attr('fill', d => this.colorScale(d.domain))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .call(this.drag())
      .on('click', (event, d) => this.onNodeClick(d))
      .on('mouseover', (event, d) => this.onNodeHover(d, true))
      .on('mouseout', (event, d) => this.onNodeHover(d, false));
    
    this.nodeElements = nodesEnter.merge(nodes);
    
    const labels = this.labelsGroup.selectAll('text')
      .data(this.nodes, d => d.id);
    
    labels.exit().remove();
    
    const labelsEnter = labels.enter().append('text')
      .attr('class', 'label')
      .attr('text-anchor', 'middle')
      .attr('dy', -15)
      .attr('font-size', '10px')
      .attr('fill', '#aaa')
      .text(d => d.title.substring(0, 20));
    
    this.labelElements = labelsEnter.merge(labels);
    
    this.simulation.nodes(this.nodes).on('tick', () => this.tick());
    this.simulation.force('link').links(this.links);
    this.simulation.alpha(1).restart();
  }
  
  tick() {
    this.linkElements
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    
    this.nodeElements
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);
    
    this.labelElements
      .attr('x', d => d.x)
      .attr('y', d => d.y);
  }
  
  drag() {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }
  
  onNodeClick(node) {
    showSidebar(node);
  }
  
  onNodeHover(node, isOver) {
    if (isOver) {
      this.nodeElements.attr('opacity', d => {
        if (d.id === node.id) return 1;
        const connected = this.links.some(l => 
          (l.source.id === node.id && l.target.id === d.id) ||
          (l.target.id === node.id && l.source.id === d.id)
        );
        return connected ? 1 : 0.3;
      });
      this.linkElements.attr('opacity', l => 
        l.source.id === node.id || l.target.id === node.id ? 1 : 0.1
      );
    } else {
      this.nodeElements.attr('opacity', 1);
      this.linkElements.attr('opacity', 0.6);
    }
  }
  
  updateStats() {
    document.getElementById('statsNodes').textContent = `${this.nodes.length} memories`;
    document.getElementById('statsEdges').textContent = `${this.links.length} connections`;
  }
  
  highlightSearch(query) {
    if (!query) {
      this.nodeElements.attr('opacity', 1);
      return;
    }
    const lowerQuery = query.toLowerCase();
    this.nodeElements.attr('opacity', d => 
      d.title.toLowerCase().includes(lowerQuery) ? 1 : 0.2
    );
  }
}

let graph;
let currentThreshold = 0.7;

document.addEventListener('DOMContentLoaded', () => {
  graph = new MemoryGraph('graph');
  initUI();
  loadGraph();
  checkHealth();
});

function initUI() {
  document.getElementById('refreshBtn').addEventListener('click', loadGraph);
  document.getElementById('closeSidebar').addEventListener('click', hideSidebar);
  document.getElementById('settingsBtn').addEventListener('click', showSettings);
  document.getElementById('closeSettings').addEventListener('click', hideSettings);
  document.getElementById('saveSettings').addEventListener('click', saveSettings);
  
  document.getElementById('searchInput').addEventListener('input', (e) => {
    graph.highlightSearch(e.target.value);
  });
  
  document.getElementById('thresholdInput').addEventListener('input', (e) => {
    document.getElementById('thresholdValue').textContent = e.target.value;
  });
  
  document.getElementById('deleteMemory').addEventListener('click', async () => {
    const id = document.getElementById('deleteMemory').dataset.memoryId;
    if (id && confirm('Delete this memory?')) {
      await API.deleteMemory(id);
      hideSidebar();
      loadGraph();
    }
  });
  
  const savedKey = localStorage.getItem('apiKey');
  const savedUrl = localStorage.getItem('apiUrl');
  if (savedKey) document.getElementById('apiKeyInput').value = savedKey;
  if (savedUrl) document.getElementById('apiUrlInput').value = savedUrl;
}

async function loadGraph() {
  try {
    await graph.loadData(currentThreshold);
    document.getElementById('status').textContent = 'Connected';
    document.getElementById('status').classList.add('connected');
  } catch (error) {
    document.getElementById('status').textContent = 'Error loading data';
    document.getElementById('status').classList.add('error');
  }
}

async function checkHealth() {
  try {
    await API.healthCheck();
    document.getElementById('status').textContent = 'Connected';
    document.getElementById('status').classList.add('connected');
  } catch (error) {
    document.getElementById('status').textContent = 'Disconnected';
    document.getElementById('status').classList.add('error');
  }
}

async function showSidebar(node) {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.remove('hidden');
  
  document.getElementById('memoryTitle').textContent = node.title;
  document.getElementById('memoryDomain').textContent = node.domain;
  document.getElementById('memoryDomain').style.backgroundColor = graph.colorScale(node.domain);
  
  try {
    const memory = await API.getMemory(node.id);
    document.getElementById('memorySummary').textContent = memory.summary || 'No summary available';
    document.getElementById('memoryContent').textContent = memory.content.substring(0, 500) + '...';
    document.getElementById('memoryLink').href = memory.url;
    document.getElementById('memoryDate').textContent = new Date(memory.created_at).toLocaleDateString();
    document.getElementById('deleteMemory').dataset.memoryId = memory.id;
  } catch (error) {
    document.getElementById('memorySummary').textContent = 'Error loading details';
  }
}

function hideSidebar() {
  document.getElementById('sidebar').classList.add('hidden');
}

function showSettings() {
  document.getElementById('settingsModal').classList.remove('hidden');
}

function hideSettings() {
  document.getElementById('settingsModal').classList.add('hidden');
}

function saveSettings() {
  const apiKey = document.getElementById('apiKeyInput').value;
  const apiUrl = document.getElementById('apiUrlInput').value;
  currentThreshold = parseFloat(document.getElementById('thresholdInput').value);
  
  API.setConfig(apiUrl, apiKey);
  hideSettings();
  loadGraph();
}

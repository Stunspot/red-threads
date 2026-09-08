"""Run actual bundled JS projections and route geometry without claiming browser evidence."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "red-threads" / "assets" / "atlas.html"

@unittest.skipUnless(shutil.which("node"), "Node is optional for executable renderer projections")
class InvestigationGeometryTests(unittest.TestCase):
    def run_js(self, checks):
        template = TEMPLATE.read_text(encoding="utf-8")
        core = template.split("/* INVESTIGATION CORE START:", 1)[1].split("*/", 1)[1].split("/* INVESTIGATION CORE END */", 1)[0]
        result = subprocess.run([shutil.which("node"), "-"], input="const assert=require('node:assert/strict');\n" + core + checks, text=True, encoding="utf-8", capture_output=True, timeout=40)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout

    def test_complete_script_compiles(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        script = html.split('</script><script>', 1)[1].split('</script>', 1)[0]
        result = subprocess.run([shutil.which("node"), "--check"], input=script, text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_curation_preserves_sparse_hubs_order_and_uncapped_explicit_nodes(self):
        self.run_js(r"""
const records=Array.from({length:16},(_,i)=>({id:'n'+i,label:'Actor '+i,group:'Funds'}));
records.push({id:'z',label:'Decision',group:'Policy'});
const es=records.slice(1,16).map(n=>({source:n.id,target:'n0'}));
const views={group_order:['Policy','Funds'],group_hubs:{Funds:'n15'},overview:{Funds:['n14','n13','n12','n11','n10','n9','n8','n7','n6','n5','n4']},overview_limit:3};
assert.deepEqual(orderedGroups(records,views),['Policy','Funds']);
const selected=overviewSelection(records.filter(n=>n.group==='Funds'),es,views,['n3','n2']);
assert.equal(selected[0].id,'n15');
assert.deepEqual(selected.slice(1,4).map(n=>n.id),['n14','n13','n12']);
assert.equal(selected.length,14);
assert.ok(selected.some(n=>n.id==='n2'));
assert.ok(!selected.some(n=>n.id==='n0'),'degree must not displace explicit curation');
assert.equal(overviewSelection(records.filter(n=>n.group==='Funds'),es,{},[]).length,9);
assert.equal(overviewSelection(records.filter(n=>n.group==='Funds'),es,{},[])[0].id,'n0');
assert.equal(overviewSelection([{id:'x',label:'Reserved group',group:'constructor'}],[],{overview:{}},[])[0].id,'x');
""")

    def test_full_correction_frontier_multiple_origins_and_context_boundary(self):
        self.run_js(r"""
const d={sources:[{id:'a'},{id:'b'},{id:'copy',origin_id:'a',origin_ids:['a','b']}],nodes:[{id:'named'},{id:'premise',depends_on:['sources:copy']}],edges:[{id:'pay',source:'named',target:'premise',source_ids:['copy'],status:'documented',hypothesis_ids:['h']},{id:'indirect',status:'inferred',depends_on:['hypotheses:h']},{id:'unrelated',source_ids:['b'],status:'documented'}],hypotheses:[{id:'h',supports:['pay']}],games:[{id:'g',depends_on:['edges:indirect']},{id:'opaque',summary:'Basis only in prose'}],leads:[{id:'next',depends_on:['games:g']},{id:'context',node_ids:['premise'],status:'open'}]};
const result=dependencyImpact(d,['sources:a']);
assert.deepEqual(new Set(result.ids.sources),new Set(['a','copy']));
for(const token of ['nodes:premise','edges:pay','hypotheses:h','edges:indirect','games:g','leads:next'])assert.ok(result.affected.includes(token),token);
for(const token of ['nodes:named','sources:b','edges:unrelated','leads:context'])assert.ok(!result.affected.includes(token),token);
assert.ok(result.untracked.includes('games:opaque'));
assert.deepEqual(sourceParents(d.sources[2]),['a','b']);
const before=JSON.stringify(d);dependencyImpact(d,['sources:b']);assert.equal(JSON.stringify(d),before,'projection must not mutate evidence');
""")

    def test_same_case_view_validation_and_changed_case_resume(self):
        self.run_js(r"""
const d={case:{id:'case-one',updated_at:'2026-09-08'},nodes:[{id:'a',group:'Funds'},{id:'b',group:'Policy'}],edges:[{id:'ab',layer:'money'}],sources:[{id:'s'}],hypotheses:[{id:'h'}],leads:[],games:[]};
const raw={format:'red-threads-view-2',case_id:'case-one',case_updated_at:'2026-09-07',tab:'hypotheses',mode:'node',focus:'a',group:null,selected_edge:'ab',selected_source:'s',selected_record:{collection:'hypotheses',id:'h'},pinned_nodes:['b'],filters:{date:'2026-09-08',include_unknown_intervals:true,layers:['money'],statuses:['documented']},structural_removal:null,path:{from:'a',to:'b'}};
const v=validateView(raw,d);assert.equal(v.changed,true);assert.deepEqual(v.pins,['b']);assert.deepEqual(v.selected,{collection:'hypotheses',id:'h'});
for(const patch of [{case_id:'another-case'},{focus:'absent'},{selected_record:{collection:'games',id:'h'}},{pinned_nodes:['missing']},{mode:'trace',path:{from:'a'}},{filters:{...raw.filters,date:'2026-02-31'}},{filters:{...raw.filters,layers:['script']}},{structural_removal:'a'}])assert.throws(()=>validateView({...raw,...patch},d));
const old={...raw,format:'red-threads-view-1'};delete old.pinned_nodes;delete old.selected_record;assert.equal(validateView(old,d).focus,'a');
""")

    def test_dense_district_and_obstacle_routes_at_two_widths(self):
        self.run_js(r"""
const records=Array.from({length:38},(_,i)=>({id:'n'+i,label:i%7===0?'Long institutional actor with scoped public role '+i:'Actor '+i}));
const edges=records.slice(1).map((n,i)=>({id:'e'+i,source:'n'+Math.floor(i/3),target:n.id}));
for(const w of [440,950]){
 const {points,height}=relaxDistrict(records,edges,w),all=[...points.values()];
 assert.equal(points.size,38);
 for(let i=0;i<all.length;i++)for(let j=i+1;j<all.length;j++)assert.equal(boxesOverlap(all[i],all[j],10),false,'labels overlap at width '+w);
 let routed=0;
 for(const e of edges){const a=points.get(e.source),b=points.get(e.target),route=routeBetween(a,b,points.values(),w,height);if(route.unresolved)continue;routed++;assert.ok(route.d);for(let i=1;i<route.points.length;i++)for(const obstacle of all.filter(p=>p!==a&&p!==b))assert.equal(segmentHits(route.points[i-1],route.points[i],obstacle),false,'route crossed a label');}
 assert.ok(routed>=edges.length*.9,'representative graph must mostly route: '+routed+'/'+edges.length+' at '+w);
}
const a={x:50,y:200,w:60,h:40},b={x:550,y:200,w:60,h:40},wall={x:300,y:200,w:280,h:440};
const blocked=routeBetween(a,b,[a,b,wall],600,400);assert.equal(blocked.unresolved,true);assert.equal(blocked.d,undefined,'unresolved paths must not masquerade as safe arrows');
""")

if __name__ == '__main__':
    unittest.main()

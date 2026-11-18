-- Test harness only; production plugin has no loadstring or generated-code execution.
local made={}
local function event()
 local e={listeners={}}
 function e:Connect(fn) table.insert(self.listeners,fn);return {Disconnect=function()end} end
 function e:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
 return e
end
local mt={}
local methods={}
function methods:SetAttribute(k,v) self.attrs[k]=v end
function methods:GetAttribute(k) return self.attrs[k] end
function methods:WaitForChild(name) return self.children[name] end
function methods:GetChildren() local result={};for _,v in pairs(self.children) do table.insert(result,v) end;return result end
function methods:Destroy() self.destroyed=true end
mt.__index=function(t,k)return methods[k] or t.props[k] end
mt.__newindex=function(t,k,v)
 if FAIL_SCRIPT_SOURCE and k=="Source" and (t.class=="Script" or t.class=="LocalScript") then error("Test: script injection denied") end
 t.props[k]=v
 if k=="Parent" and v then v.children[t.props.Name or t.class]=t end
end
local Instance={new=function(class)
 local obj=setmetatable({class=class,props={},children={},attrs={},Destroying=event()},mt)
 table.insert(made,obj);return obj
end}
local unload=event()
local toolbarButton={Click=event(),SetActive=function()end}
local plugin={Unloading=unload,CreateToolbar=function()return {CreateButton=function()return toolbarButton end}end,CreateDockWidgetPluginGui=function()return Instance.new("DockWidget") end}
local workspace=Instance.new("Workspace")
local scripts=Instance.new("StarterPlayerScripts");scripts.Name="StarterPlayerScripts"
local starter=Instance.new("StarterPlayer");scripts.Parent=starter
local results={}
local polled=false
local Http={UrlEncode=function(_,x)return x end,JSONEncode=function(_,x)return x end,JSONDecode=function(_,x)return x end}
function Http:RequestAsync(req)
 assert(req.Headers["X-Jarvis-Plugin-Version"]=="2","missing version handshake")
 local body
 if string.find(req.Url,"/poll",1,true) then
  body={job=not polled and JOB or nil};polled=true
 else
  table.insert(results,req.Body)
  body={ok=true}
  if CANCEL_AFTER and req.Body.status=="progress" and req.Body.count>=CANCEL_AFTER then body={ok=false,cancelled=true} end
 end
 return {Success=true,Body=body}
end
local services={HttpService=Http,ChangeHistoryService={SetWaypoint=function()end},RunService={IsRunning=function()return false end},Selection={Set=function()end},StarterPlayer=starter}
local game={Name="Mock Studio",GetService=function(_,key)assert(services[key],key);return services[key] end}
local function passthrough(...)return {...}end
local Vector3={new=passthrough}
local Color3={fromRGB=passthrough}
local DockWidgetPluginGuiInfo={new=passthrough}
local UDim2={fromScale=passthrough}
local Enum={InitialDockState={Right="right"},Material={Neon="neon",SmoothPlastic="smooth"},PartType={Ball="ball"}}
local task={spawn=function(fn)fn()end,wait=function(seconds)if seconds==2 then unload:Fire() end end}

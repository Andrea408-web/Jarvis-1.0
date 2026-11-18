-- JARVIS local Studio bridge. No loadstring, generated Lua, filesystem or cloud.
local Http = game:GetService("HttpService")
local History = game:GetService("ChangeHistoryService")
local BASE = "__BRIDGE_URL__"
local KEY = "__BRIDGE_KEY__"
local alive = true
plugin.Unloading:Connect(function() alive = false end)
local toolbar = plugin:CreateToolbar("Jarvis")
local toggle = toolbar:CreateButton("Jarvis verbinden", "Lokale Jarvis-Brücke pausieren/fortsetzen", "")
local enabled = true
toggle:SetActive(true)
toggle.Click:Connect(function() enabled = not enabled; toggle:SetActive(enabled) end)
local function request(path, body)
 local response = Http:RequestAsync({Url=BASE..path,Method=body and "POST" or "GET",Headers={["X-Jarvis-Studio"]=KEY,["Content-Type"]="application/json"},Body=body and Http:JSONEncode(body) or nil})
 if not response.Success then error("Jarvis-Brücke antwortet nicht. Plugin neu über Jarvis verbinden.") end
 return Http:JSONDecode(response.Body)
end
local gameplay = [==[
local Players=game:GetService("Players")
local root=script.Parent
local function init(player)
 local stats=player:FindFirstChild("leaderstats")
 if not stats then stats=Instance.new("Folder");stats.Name="leaderstats";stats.Parent=player end
 if not stats:FindFirstChild("JarvisCoins") then local score=Instance.new("IntValue");score.Name="JarvisCoins";score.Parent=stats end
 player.RespawnLocation=root:FindFirstChildWhichIsA("SpawnLocation")
end
Players.PlayerAdded:Connect(init)
for _,p in ipairs(Players:GetPlayers()) do init(p) end
for _,part in ipairs(root:GetChildren()) do
 if part:GetAttribute("JarvisKind")=="coin" then
  local taken={}
  part.Touched:Connect(function(hit)
   local player=Players:GetPlayerFromCharacter(hit.Parent)
   if not player or taken[player.UserId] then return end
   taken[player.UserId]=true
   local score=player:FindFirstChild("leaderstats") and player.leaderstats:FindFirstChild("JarvisCoins")
   if score then score.Value+=1 end
   task.delay(4,function() taken[player.UserId]=nil end)
  end)
 elseif part:GetAttribute("JarvisKind")=="goal" then
  part.Touched:Connect(function(hit)
   local player=Players:GetPlayerFromCharacter(hit.Parent)
   if player and not player:GetAttribute("JarvisParcoursGeschafft") then
    player:SetAttribute("JarvisParcoursGeschafft",true)
    local gui=Instance.new("ScreenGui");gui.Name="JarvisZiel";gui.ResetOnSpawn=false
    local label=Instance.new("TextLabel");label.Size=UDim2.fromScale(.5,.12);label.Position=UDim2.fromScale(.25,.12);label.BackgroundColor3=Color3.fromRGB(35,59,25);label.TextColor3=Color3.fromRGB(225,241,193);label.TextScaled=true;label.Text="Ziel erreicht, Sir!";label.Parent=gui;gui.Parent=player:WaitForChild("PlayerGui")
    task.delay(5,function() gui:Destroy() end)
   end
  end)
 end
end
]==]
local function build(job)
 local scene=job.scene
 assert(type(scene)=="table" and type(scene.parts)=="table" and #scene.parts<=42,"Ungültiger Bauplan")
 local folder=Instance.new("Model")
 folder.Name="JARVIS - "..string.sub(scene.name,1,80).." - "..string.sub(job.id,1,6)
 folder.Parent=workspace
 local count=0
 local function report(status,message)
  request("/result",{id=job.id,status=status,count=count,message=message})
 end
 local ok,err=pcall(function()
  History:SetWaypoint("Vor Jarvis-Parcours")
  for _,spec in ipairs(scene.parts) do
   if not alive or not enabled then error("Bauen im Studio-Plugin pausiert. Teilmodell bleibt sichtbar.") end
   assert(spec.kind=="spawn" or spec.kind=="platform" or spec.kind=="coin" or spec.kind=="goal","Unbekanntes Teil")
   local p=Instance.new(spec.kind=="spawn" and "SpawnLocation" or "Part")
   p.Name=spec.kind.."_"..tostring(count+1);p.Anchored=true
   p.Size=Vector3.new(table.unpack(spec.size));p.Position=Vector3.new(table.unpack(spec.position))
   p:SetAttribute("JarvisKind",spec.kind)
   p.Color=spec.kind=="coin" and Color3.fromRGB(248,207,69) or spec.kind=="goal" and Color3.fromRGB(118,226,142) or Color3.fromRGB(73,104,70)
   p.Material=spec.kind=="coin" and Enum.Material.Neon or Enum.Material.SmoothPlastic
   if spec.kind=="coin" then p.Shape=Enum.PartType.Ball;p.CanCollide=false end
   p.Parent=folder;count+=1
   report("progress",tostring(count).." Teile tatsächlich im Studio erstellt")
   task.wait(.10)
  end
  local server=Instance.new("Script");server.Name="JarvisGameplay";server.Source=gameplay;server.Parent=folder
  game:GetService("Selection"):Set({folder})
  History:SetWaypoint("Jarvis-Parcours erstellt")
  report("done","Parcours mit Spawn, Plattformen, Münzpunkten und Ziel erstellt. In Studio mit Play testen; noch nicht veröffentlicht.")
 end)
 if not ok then pcall(function() report("error",string.sub(tostring(err),1,480)) end) end
end
-- Studio, not a running Roblox game; explicit installation is required.
task.spawn(function()
 while alive do
  if enabled then
   local ok,data=pcall(function() return request("/poll") end)
   if ok and data.job then build(data.job) end
  end
  task.wait(2)
 end
end)

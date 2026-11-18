-- JARVIS local Studio bridge. No loadstring, generated Lua, filesystem or cloud.
local Http = game:GetService("HttpService")
local History = game:GetService("ChangeHistoryService")
local BASE = "__BRIDGE_URL__"
local KEY = "__BRIDGE_KEY__"
local alive = true
plugin.Unloading:Connect(function() alive = false end)
local toolbar = plugin:CreateToolbar("Jarvis")
local toggle = toolbar:CreateButton("Jarvis verbinden", "Lokale Jarvis-Brücke pausieren/fortsetzen", "", "Jarvis")
local widget=plugin:CreateDockWidgetPluginGui("JarvisStudioV2",DockWidgetPluginGuiInfo.new(Enum.InitialDockState.Right,true,false,320,180,240,120))
widget.Title="Jarvis · Studio-Brücke v2"
local statusLabel=Instance.new("TextLabel");statusLabel.Size=UDim2.fromScale(1,1);statusLabel.BackgroundColor3=Color3.fromRGB(17,28,18);statusLabel.TextColor3=Color3.fromRGB(220,236,182);statusLabel.TextWrapped=true;statusLabel.TextSize=15;statusLabel.Text="Warte auf Jarvis …";statusLabel.Parent=widget
local function show(text) statusLabel.Text=text end
local enabled = true
toggle:SetActive(true)
toggle.Click:Connect(function() enabled = not enabled; toggle:SetActive(enabled);show(enabled and "Verbindung wird geprüft …" or "Pausiert. Bereits gebaute Teile bleiben erhalten.") end)
local function request(path, body)
 local response = Http:RequestAsync({Url=BASE..path,Method=body and "POST" or "GET",Headers={["X-Jarvis-Studio"]=KEY,["X-Jarvis-Plugin-Version"]="2",["X-Jarvis-Place"]=Http:UrlEncode(game.Name),["Content-Type"]="application/json"},Body=body and Http:JSONEncode(body) or nil})
 if not response.Success then error("Jarvis-Brücke antwortet nicht. In Jarvis auf Vorhandenes Plugin verbinden tippen.") end
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
local heroClient=[====[__HERO_CLIENT__]====]
local heroServer=[====[__HERO_SERVER__]====]
local kinds={spawn=true,platform=true,coin=true,goal=true,ground=true,road=true,building=true,roof=true,window=true,checkpoint=true}
local function build(job)
 local count=0
 local gameReady=false
 local folder=nil
 local phase="geometry"
 local function report(status,message)
  local result=request("/result",{id=job.id,status=status,count=count,message=message,gameplay_ready=gameReady})
  if result.cancelled then error("Auftrag in Jarvis gestoppt. Teilmodell bleibt stehen.") end
 end
 local ok,err=pcall(function()
  assert(not game:GetService("RunService"):IsRunning(),"Bitte Play zuerst stoppen. Gebaut wird im Studio-Bearbeitungsmodus.")
  local scene=job.scene
  assert(type(scene)=="table" and type(scene.parts)=="table" and #scene.parts<=256,"Ungültiger Bauplan")
  if scene.kind=="hero-city" then
   for _,model in ipairs(workspace:GetChildren()) do
    assert(not model:GetAttribute("JarvisHeroStarter"),"Hier steht bereits eine Jarvis-Stadt. Für einen neuen Prototyp ein leeres Projekt öffnen oder das alte Jarvis-Modell samt Clientskript bewusst entfernen.")
   end
  end
  History:SetWaypoint("Vor Jarvis-Bau")
  folder=Instance.new("Model");folder.Name="JARVIS - "..string.sub(scene.name,1,80).." - "..string.sub(job.id,1,6);folder.Parent=workspace
  if scene.kind=="hero-city" then folder:SetAttribute("JarvisHeroStarter",true) end
  if scene.kind=="hero-city" then pcall(function()
   if workspace.CurrentCamera then workspace.CurrentCamera.CFrame=CFrame.lookAt(Vector3.new(220,170,240),Vector3.new(0,30,0)) end
  end) end
  local order=0
  for _,spec in ipairs(scene.parts) do
   if not alive or not enabled then error("Bauen im Studio-Plugin pausiert. Teilmodell bleibt sichtbar.") end
   assert(kinds[spec.kind],"Unbekanntes Teil")
   assert(type(spec.position)=="table" and #spec.position==3 and type(spec.size)=="table" and #spec.size==3,"Ungültige Geometrie")
   for i=1,3 do assert(type(spec.position[i])=="number" and math.abs(spec.position[i])<=3000 and type(spec.size[i])=="number" and spec.size[i]>0 and spec.size[i]<=500,"Geometrie außerhalb der Grenzen") end
   local p=Instance.new(spec.kind=="spawn" and "SpawnLocation" or "Part")
   p.Name=spec.kind.."_"..tostring(count+1);p.Anchored=true;p.Size=Vector3.new(table.unpack(spec.size));p.Position=Vector3.new(table.unpack(spec.position));p:SetAttribute("JarvisKind",spec.kind)
   p.Color=spec.kind=="coin" and Color3.fromRGB(248,207,69) or spec.kind=="goal" and Color3.fromRGB(118,226,142) or Color3.fromRGB(73,104,70)
   if spec.color then for _,v in ipairs(spec.color) do assert(type(v)=="number" and v>=0 and v<=255,"Ungültige Farbe") end;p.Color=Color3.fromRGB(table.unpack(spec.color)) end
   p.Material=(spec.kind=="coin" or spec.kind=="window" or spec.kind=="checkpoint") and Enum.Material.Neon or Enum.Material.SmoothPlastic
   if spec.kind=="coin" or spec.kind=="checkpoint" then p.Shape=Enum.PartType.Ball;p.CanCollide=false end
   if spec.kind=="checkpoint" then order=order+1;p:SetAttribute("JarvisOrder",order) end
   if spec.kind=="spawn" then p.Neutral=true;p.Duration=0 end
   p.Parent=folder;count=count+1
   show("Baue direkt in "..game.Name.."\n"..tostring(count).." / "..tostring(#scene.parts).." Teile")
   report("progress",tostring(count).." Teile im geöffneten Studio erstellt")
   task.wait(.025)
  end
  phase="scripts"
  local server=Instance.new("Script");server.Name="JarvisGameplay";server.Source=scene.kind=="hero-city" and heroServer or gameplay;server.Parent=folder
  if scene.kind=="hero-city" then
   local client=Instance.new("LocalScript");client.Name="JarvisHero_"..string.sub(job.id,1,8);client.Source=heroClient;client:SetAttribute("JarvisWorld",folder.Name);client:SetAttribute("JarvisHeroTemplate",true);client.Parent=game:GetService("StarterPlayer"):WaitForChild("StarterPlayerScripts")
  end
  gameReady=true
  game:GetService("Selection"):Set({folder})
  History:SetWaypoint("Jarvis-Spielbausteine erstellt")
  local message=scene.kind=="hero-city" and "Stadt, Serverlogik und Spielersteuerung direkt in Studio eingesetzt. Mit Play testen: Q Schwingen, E Dash, Space Sprung/Wandlauf, R Zurück. Nicht veröffentlicht." or "Parcours und Spielskript direkt in Studio erstellt. Mit Play testen und selbst speichern."
  report("done",message);show(message)
 end)
 if not ok and phase=="scripts" and not gameReady and folder then folder:Destroy();err="Spielskripte konnten nicht eingesetzt werden. Neuer Bauentwurf zurückgenommen. In Studio die Skript-Berechtigung des Plugins prüfen: "..tostring(err) end
 if not ok then show("Bau nicht abgeschlossen:\n"..tostring(err));pcall(function() report("error",string.sub(tostring(err),1,480)) end) end
end
-- Studio, not a running Roblox game; explicit installation is required.
task.spawn(function()
 while alive do
  if enabled then
   local ok,data=pcall(function() return request("/poll") end)
   if ok and data.job then build(data.job) elseif not ok then show("Nicht verbunden:\n"..tostring(data).."\nJarvis starten und Vorhandenes Plugin verbinden wählen.") end
  end
  task.wait(2)
 end
end)

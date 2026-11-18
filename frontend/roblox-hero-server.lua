-- Original JARVIS starter mechanics. Server validates checkpoint touches.
local Players=game:GetService("Players")
local Run=game:GetService("RunService")
local root=script.Parent
local spawn=root:FindFirstChildWhichIsA("SpawnLocation")
local nextPoint={}
local started={}
local connections={}
local running=true
local function init(player)
 nextPoint[player]=1;started[player]=nil
 player:SetAttribute("JarvisRacePoint",0)
 player:SetAttribute("JarvisRaceTime",0)
 player:SetAttribute("JarvisRaceFinished",false)
 if spawn then player.RespawnLocation=spawn end
 local function character(char)
  local hum=char:WaitForChild("Humanoid",10)
  if hum then hum.WalkSpeed=24;hum.UseJumpPower=true;hum.JumpPower=55 end
 end
 table.insert(connections,player.CharacterAdded:Connect(character))
 if player.Character then task.spawn(character,player.Character) end
end
for _,p in ipairs(Players:GetPlayers()) do init(p) end
table.insert(connections,Players.PlayerAdded:Connect(init))
table.insert(connections,Players.PlayerRemoving:Connect(function(p) nextPoint[p]=nil;started[p]=nil end))
local checkpoints={}
for _,part in ipairs(root:GetChildren()) do
 if part:GetAttribute("JarvisKind")=="checkpoint" then table.insert(checkpoints,part) end
end
table.sort(checkpoints,function(a,b)return (a:GetAttribute("JarvisOrder") or 0)<(b:GetAttribute("JarvisOrder") or 0) end)
for i,part in ipairs(checkpoints) do
 local gui=Instance.new("BillboardGui");gui.Size=UDim2.fromOffset(110,45);gui.StudsOffset=Vector3.new(0,5,0);gui.AlwaysOnTop=true;gui.Parent=part
 local label=Instance.new("TextLabel");label.Size=UDim2.fromScale(1,1);label.BackgroundTransparency=1;label.TextColor3=Color3.fromRGB(255,226,125);label.TextScaled=true;label.Text=tostring(i).." / "..tostring(#checkpoints);label.Parent=gui
 table.insert(connections,part.Touched:Connect(function(hit)
  local char=hit:FindFirstAncestorOfClass("Model")
  local p=char and Players:GetPlayerFromCharacter(char)
  if not p or nextPoint[p]~=i then return end
  local torso=char:FindFirstChild("HumanoidRootPart")
  if not torso or (torso.Position-part.Position).Magnitude>14 then return end
  if i==1 then started[p]=os.clock() end
  nextPoint[p]=i+1;p:SetAttribute("JarvisRacePoint",i)
  if i==#checkpoints then p:SetAttribute("JarvisRaceFinished",true);p:SetAttribute("JarvisRaceTime",os.clock()-(started[p] or os.clock())) end
 end))
end
local heartbeatElapsed=0
table.insert(connections,Run.Heartbeat:Connect(function(dt)
 heartbeatElapsed=heartbeatElapsed+dt;if heartbeatElapsed<.1 then return end;heartbeatElapsed=0
 for p,t in pairs(started) do
  if p.Parent and not p:GetAttribute("JarvisRaceFinished") then p:SetAttribute("JarvisRaceTime",os.clock()-t) end
 end
end))
root.Destroying:Connect(function() running=false;for _,c in ipairs(connections) do c:Disconnect() end end)

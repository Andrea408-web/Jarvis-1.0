-- Original local prototype controller: bounded rope swing, wall assist, double jump.
local Players=game:GetService("Players")
local Run=game:GetService("RunService")
local Input=game:GetService("UserInputService")
local Actions=game:GetService("ContextActionService")
local player=Players.LocalPlayer
local worldName=script:GetAttribute("JarvisWorld")
local world=workspace:WaitForChild(worldName,15)
if not world then return end
local gui=Instance.new("ScreenGui");gui.Name="JarvisHeroHUD";gui.ResetOnSpawn=false;gui.Parent=player:WaitForChild("PlayerGui")
local label=Instance.new("TextLabel");label.Size=UDim2.new(.68,0,0,92);label.Position=UDim2.fromScale(.16,.025);label.BackgroundColor3=Color3.fromRGB(15,30,38);label.BackgroundTransparency=.15;label.TextColor3=Color3.fromRGB(204,243,235);label.TextSize=16;label.TextWrapped=true;label.Parent=gui
local corner=Instance.new("UICorner");corner.CornerRadius=UDim.new(0,12);corner.Parent=label
local energy=100
local character,hum,torso
local rope,anchor,att0,att1
local jumps=0
local wallHeld=false
local alive=true
local connections={}
local prefix="JarvisHero_"..world.Name
local function release()
 if rope then rope:Destroy();rope=nil end
 if att0 then att0:Destroy();att0=nil end
 if anchor then anchor:Destroy();anchor=nil end
 att1=nil
end
local function cast(origin,vector)
 local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Exclude;params.FilterDescendantsInstances={character};params.IgnoreWater=true
 return workspace:Raycast(origin,vector,params)
end
local function swing(_,state)
 if state==Enum.UserInputState.End or state==Enum.UserInputState.Cancel then release();return Enum.ContextActionResult.Sink end
 if state~=Enum.UserInputState.Begin then return Enum.ContextActionResult.Sink end
 if not torso or not hum or hum.Health<=0 or energy<10 then return Enum.ContextActionResult.Sink end
 release()
 local camera=workspace.CurrentCamera
 local point=nil
 if camera then
  local hit=cast(camera.CFrame.Position,camera.CFrame.LookVector*140)
  if hit and hit.Instance:IsDescendantOf(world) and hit.Position.Y>torso.Position.Y+5 then point=hit.Position end
 end
 if not point then
  local best=math.huge
  for _,part in ipairs(world:GetChildren()) do
   if part:IsA("BasePart") and part:GetAttribute("JarvisKind")=="roof" then
    local near=Vector3.new(math.clamp(torso.Position.X-part.Position.X,-part.Size.X/2,part.Size.X/2),3,math.clamp(torso.Position.Z-part.Position.Z,-part.Size.Z/2,part.Size.Z/2));local target=part.Position+near;local delta=target-torso.Position;local distance=delta.Magnitude
    if delta.Y>7 and distance>12 and distance<120 then
     local sight=cast(torso.Position,delta)
     if not sight or sight.Instance==part then
      local score=distance-(camera and camera.CFrame.LookVector:Dot(delta.Unit)*25 or 0)
      if score<best then best=score;point=target end
     end
    end
   end
  end
 end
 if not point then return Enum.ContextActionResult.Sink end
 anchor=Instance.new("Part");anchor.Name="JarvisSwingAnchor";anchor.Anchored=true;anchor.CanCollide=false;anchor.CanQuery=false;anchor.Transparency=1;anchor.Size=Vector3.new(.2,.2,.2);anchor.Position=point;anchor.Parent=workspace
 att0=Instance.new("Attachment");att0.Parent=torso;att1=Instance.new("Attachment");att1.Parent=anchor
 rope=Instance.new("RopeConstraint");rope.Attachment0=att0;rope.Attachment1=att1;rope.Length=math.max(10,(torso.Position-point).Magnitude*.92);rope.Visible=true;rope.Thickness=.1;rope.Color=BrickColor.new("Cyan");rope.Parent=torso
 local forward=camera and camera.CFrame.LookVector or torso.CFrame.LookVector
 torso.AssemblyLinearVelocity=torso.AssemblyLinearVelocity+Vector3.new(forward.X,0,forward.Z)*28+Vector3.new(0,16,0)
 return Enum.ContextActionResult.Sink
end
local function dash(_,state)
 if state==Enum.UserInputState.Begin and torso and hum and energy>=30 then
  energy=energy-30;local dir=hum.MoveDirection
  if dir.Magnitude<.1 then dir=torso.CFrame.LookVector end
  torso.AssemblyLinearVelocity=dir.Unit*95+Vector3.new(0,12,0)
 end
 return Enum.ContextActionResult.Sink
end
local function jump(_,state)
 if state==Enum.UserInputState.Begin and torso and hum then
  wallHeld=true
  if hum.FloorMaterial~=Enum.Material.Air then jumps=1;hum.Jump=true
  elseif jumps<2 then jumps=2;hum:ChangeState(Enum.HumanoidStateType.Jumping);local v=torso.AssemblyLinearVelocity;torso.AssemblyLinearVelocity=Vector3.new(v.X,53,v.Z) end
 elseif state==Enum.UserInputState.End or state==Enum.UserInputState.Cancel then wallHeld=false end
 return Enum.ContextActionResult.Sink
end
local function reset(_,state)
 if state==Enum.UserInputState.Begin and character then
  release();local spawn=world:FindFirstChildWhichIsA("SpawnLocation")
  if spawn then character:PivotTo(spawn.CFrame+Vector3.new(0,5,0));if torso then torso.AssemblyLinearVelocity=Vector3.zero end end
 end
 return Enum.ContextActionResult.Sink
end
local function bind(char)
 release();character=char;hum=char:WaitForChild("Humanoid",10);torso=char:WaitForChild("HumanoidRootPart",10);jumps=0;energy=100
 if hum then table.insert(connections,hum.Died:Connect(release)) end
end
table.insert(connections,player.CharacterAdded:Connect(bind));if player.Character then task.spawn(bind,player.Character) end
Actions:BindAction(prefix.."Swing",swing,true,Enum.KeyCode.Q)
Actions:BindAction(prefix.."Dash",dash,true,Enum.KeyCode.E)
Actions:BindAction(prefix.."Jump",jump,true,Enum.KeyCode.Space,Enum.KeyCode.ButtonA)
Actions:BindAction(prefix.."Reset",reset,true,Enum.KeyCode.R)
Actions:SetTitle(prefix.."Swing","Schwingen");Actions:SetTitle(prefix.."Dash","Dash");Actions:SetTitle(prefix.."Jump","Sprung");Actions:SetTitle(prefix.."Reset","Zurück")
Actions:SetPosition(prefix.."Swing",UDim2.fromScale(.65,.6));Actions:SetPosition(prefix.."Dash",UDim2.fromScale(.83,.6));Actions:SetPosition(prefix.."Jump",UDim2.fromScale(.83,.8));Actions:SetPosition(prefix.."Reset",UDim2.fromScale(.65,.8))
table.insert(connections,Run.Heartbeat:Connect(function(dt)
 if not alive or not torso or not hum or hum.Health<=0 then return end
 if hum.FloorMaterial~=Enum.Material.Air then jumps=0 end
 if rope then
  energy=math.max(0,energy-dt*7)
  local force=hum.MoveDirection*dt*45;torso.AssemblyLinearVelocity=torso.AssemblyLinearVelocity+force
  if energy<=0 then release() end
 else energy=math.min(100,energy+dt*12) end
 if wallHeld and hum.FloorMaterial==Enum.Material.Air and hum.MoveDirection.Magnitude>.1 then
  local wall=cast(torso.Position,hum.MoveDirection*4)
  if wall and wall.Instance:IsDescendantOf(world) and math.abs(wall.Normal.Y)<.25 then
   local tangent=hum.MoveDirection-wall.Normal*hum.MoveDirection:Dot(wall.Normal)
   if tangent.Magnitude>.1 then torso.AssemblyLinearVelocity=tangent.Unit*30+Vector3.new(0,14,0)
   else torso.AssemblyLinearVelocity=Vector3.new(0,24,0) end
  end
 end
 if torso.Position.Y< -35 then reset(nil,Enum.UserInputState.Begin) end
 label.Text="NEONLÄUFER · PROTOTYP\nEnergie "..math.floor(energy).."%  |  Dächer "..tostring(player:GetAttribute("JarvisRacePoint") or 0).."/8  |  "..string.format("%.1f",player:GetAttribute("JarvisRaceTime") or 0).." s"..(player:GetAttribute("JarvisRaceFinished") and " · ZIEL!" or "\nQ halten: Schwingen · E: Dash · Space: Doppelsprung/Wand · R: Zurück")
end))
local function cleanup()
 if not alive then return end;alive=false;release()
 for _,c in ipairs(connections) do c:Disconnect() end
 for _,name in ipairs({"Swing","Dash","Jump","Reset"}) do Actions:UnbindAction(prefix..name) end
 gui:Destroy()
end
world.Destroying:Connect(cleanup);script.Destroying:Connect(cleanup)

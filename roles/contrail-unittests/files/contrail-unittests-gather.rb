#!/usr/bin/env ruby

require 'rubygems'
require 'json'

exit(0) if ENV["ZUUL_CHANGES"] !~ /refs\/changes\/([^^]*)$/
change_set = $1

json_file = "#{ENV["WORKSPACE"]}/repo/controller/ci_unittests.json"
exit(0) unless File.file?(json_file)

project = "controller"
project = "tools/sandesh" if ENV["ZUUL_PROJECT"] =~ /contrail-sandesh/
project = "tools/generateds" if ENV["ZUUL_PROJECT"] =~ /contrail-generateDS/
project = "vrouter" if ENV["ZUUL_PROJECT"] =~ /contrail-vrouter/

Dir.chdir("#{ENV["WORKSPACE"]}/repo/#{project}")

# Get the files changes in this change-set.
cmd = %{git ls-remote 2>/dev/null | \grep #{change_set} | \grep refs | awk '{print $1}' | xargs git show --pretty="format:" --name-only}

@dirs = { }
`#{cmd}`.split.each { |file|
    next if "#{project}/#{file}" !~ /(.*?\/.*?\/.*?)\//
    @dirs[$1] = true
}

# Always test for changes to generateds and vrouter projects.
@dirs["tools/generateds"] = true if project == "tools/generateds"
@dirs["vrouter"] = true if project == "vrouter"

# Load unit-tests configuration
json = JSON.parse(File.read(json_file))

# Find all applicable scons test targets
@tests = [ ]
json.each_pair { |module_name, module_data|
    skip = true
    @dirs.each_key { |dir|
        if module_data["source_directories"].include?(dir) then

            # We need to run associated tests as the path matches.
            skip = false
            break
        end
    }
    next if skip

    @tests += module_data["scons_test_targets"]
    module_data["misc_test_targets"].each { |m|
        @tests += json[m]["scons_test_targets"]
    }
}

puts @tests.sort.uniq.join(" ") unless @tests.empty?

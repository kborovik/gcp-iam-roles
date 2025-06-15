# Fish completion for gcp-iam-roles CLI tool

# Dynamic completions for role names (for --diff and --list options)
function __gcp_iam_roles_get_roles
    gcp-iam-roles _list-roles 2>/dev/null
end

# Main command completion
complete -c gcp-iam-roles -f

# Global options
complete -c gcp-iam-roles -l help -d "Show help message"

# Subcommands
complete -c gcp-iam-roles -n "not __fish_seen_subcommand_from role permission service status clear-db" -a role -d "Manage GCP IAM roles"
complete -c gcp-iam-roles -n "not __fish_seen_subcommand_from role permission service status clear-db" -a permission -d "Manage GCP IAM permissions"
complete -c gcp-iam-roles -n "not __fish_seen_subcommand_from role permission service status clear-db" -a service -d "Manage GCP services"
complete -c gcp-iam-roles -n "not __fish_seen_subcommand_from role permission service status clear-db" -a status -d "Show roles and permissions count"
complete -c gcp-iam-roles -n "not __fish_seen_subcommand_from role permission service status clear-db" -a clear-db -d "Drop database tables"

# Role subcommand options
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from role" -l search -d "Search for roles by name pattern" -r
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from role" -l sync -d "Sync predefined IAM roles and permissions from Google Cloud APIs"
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from role" -l help -d "Show help message"
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from role" -l diff -a "(__gcp_iam_roles_get_roles)" -d "Compare permissions between two roles" -x

# Permission subcommand options
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from permission" -l search -d "Search for permissions by name pattern" -r
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from permission" -l help -d "Show help message"
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from permission" -l list -a "(__gcp_iam_roles_get_roles)" -d "List all permissions for a given role" -x

# Service subcommand options
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from service" -l search -d "Search for services by name pattern" -r
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from service" -l sync -d "Sync Google Cloud services"
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from service" -l help -d "Show help message"

# Status and clear-db subcommand options
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from status" -l help -d "Show help message"
complete -c gcp-iam-roles -n "__fish_seen_subcommand_from clear-db" -l help -d "Show help message"
